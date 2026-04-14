import sys
import subprocess
import time
import requests
import os
import datetime
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QSpinBox, 
                             QPushButton, QTextEdit, QGroupBox, QLineEdit, 
                             QRadioButton, QDialog, QScrollArea, QMessageBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

# --- KONFIGURÁCIA ---
GITHUB_RAW_URL = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/DSLR_supported/devcontrol_dslr.py"
CURRENT_VERSION = "2026.4_1.3" 

class UpdateWorker(QThread):
    update_available = pyqtSignal(str)
    def run(self):
        try:
            res = requests.get(GITHUB_RAW_URL, timeout=5)
            if res.status_code == 200:
                match = re.search(r'CURRENT_VERSION = "([\d._]+)"', res.text)
                if match and match.group(1) != CURRENT_VERSION:
                    self.update_available.emit(res.text)
        except: pass

class GphotoWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, port_arg, settings, cmd_type="sequence"):
        super().__init__()
        self.port = port_arg 
        self.s = settings
        self.cmd_type = cmd_type
        self.is_running = True

    def run(self):
        if self.cmd_type == "single":
            self.execute(self.s['cmd'])
            self.finished_signal.emit(True)
            return

        self.log_signal.emit(f"--- ŠTART ASTRO SEKVENCIE v{CURRENT_VERSION} ---")
        
        # Stabilizácia: Nastavenie RAW formátu s pauzou
        self.execute(["gphoto2"] + self.port + ["--set-config", "imageformat=RAW"])
        time.sleep(1) 
        
        for i in range(1, self.s['frames'] + 1):
            if not self.is_running: break
            
            # Generovanie názvu
            now = datetime.datetime.now()
            fn = self.s['pattern']
            fn = fn.replace("%O", self.s['target'])
            fn = fn.replace("%T", self.s['type'])
            fn = fn.replace("%N", str(i).zfill(3))
            fn = fn.replace("%I", self.s['iso'])
            
            # OPRAVA: Odstránenie lomeno z času expozície pre názov súboru (kvôli 1/100)
            exp_clean = str(self.s['exp_label']).replace("/", "-")
            fn = fn.replace("%E", exp_clean)
            
            fn = fn.replace("%D", now.strftime("%Y%m%d"))
            fn = fn.replace("%H", now.strftime("%H%M%S"))
            
            # Vyčistenie názvu od nebezpečných znakov pre OS
            fn = re.sub(r'[\\/*?:"<>|]', "", fn)
            
            self.log_signal.emit(f"\nSnímka {i}/{self.s['frames']} -> {fn}.CR2")

            if self.s['shutter_val'] == "bulb":
                cmd = ["gphoto2"] + self.port + [
                    "--bulb", str(self.s['bulb_time']),
                    "--capture-image-and-download",
                    "--filename", f"{fn}.CR2"
                ]
            else:
                cmd = ["gphoto2"] + self.port + [
                    "--capture-image-and-download",
                    "--filename", f"{fn}.CR2"
                ]
            
            success = self.execute(cmd)
            if not success:
                self.log_signal.emit("Chyba komunikácie. Čakám 3s na reset a skúsim znova...")
                time.sleep(3)
                # Skúsime jeden retry pre WiFi stabilitu
                if not self.execute(cmd):
                    self.log_signal.emit("Kritická chyba spojenia.")
                    break
                
            if i < self.s['frames'] and self.is_running:
                self.log_signal.emit(f"Pauza medzi snímkami: {self.s['interval']}s")
                time.sleep(self.s['interval'])
                
        self.finished_signal.emit(True)

    def execute(self, cmd):
        self.log_signal.emit(f"> {' '.join(cmd)}")
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(p.stdout.readline, ''):
                if not self.is_running: 
                    p.terminate()
                    return False
                self.log_signal.emit(line.strip())
            p.wait()
            return p.returncode == 0
        except Exception as e:
            self.log_signal.emit(f"Systémová chyba: {e}")
            return False

    def stop(self):
        self.is_running = False

class DevControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"devcontrol_dslr v{CURRENT_VERSION}")
        self.resize(1100, 850)
        self.setup_ui()
        self.apply_astro_theme()
        
        self.up_worker = UpdateWorker()
        self.up_worker.update_available.connect(self.prompt_update)
        self.up_worker.start()

    def setup_ui(self):
        c = QWidget(); self.setCentralWidget(c); main = QVBoxLayout(c)

        # --- Sekcia 1: Pripojenie ---
        top = QHBoxLayout()
        conn_g = QGroupBox("Pripojenie (Canon 6D)")
        cl = QHBoxLayout()
        self.usb_r = QRadioButton("USB"); self.usb_r.setChecked(True)
        self.wifi_r = QRadioButton("WiFi (PTP/IP)")
        self.ip_in = QLineEdit("192.168.5.204"); self.ip_in.setEnabled(False)
        self.wifi_r.toggled.connect(lambda: self.ip_in.setEnabled(self.wifi_r.isChecked()))
        self.det_b = QPushButton("Test Spojenia"); self.det_b.clicked.connect(self.detect)
        cl.addWidget(self.usb_r); cl.addWidget(self.wifi_r); cl.addWidget(QLabel("IP:")); cl.addWidget(self.ip_in); cl.addWidget(self.det_b)
        conn_g.setLayout(cl); top.addWidget(conn_g, 4)
        
        self.help_b = QPushButton("Help/Tags"); self.help_b.clicked.connect(self.show_help)
        top.addWidget(self.help_b, 1)
        main.addLayout(top)

        # --- Sekcia 2: Nastavenia Súborov ---
        fn_g = QGroupBox("Pomenovanie súborov (Pattern)")
        fnl = QHBoxLayout()
        self.target_in = QLineEdit("IFN_Project")
        self.pattern_in = QLineEdit("%O_%T_S%N_ISO%I_%E")
        fnl.addWidget(QLabel("Objekt:")); fnl.addWidget(self.target_in)
        fnl.addWidget(QLabel("Vzor:")); fnl.addWidget(self.pattern_in)
        fn_g.setLayout(fnl); main.addWidget(fn_g)

        # --- Sekcia 3: Parametre ---
        mid = QHBoxLayout()
        exp_g = QGroupBox("Expozícia")
        el = QVBoxLayout()
        
        type_l = QHBoxLayout()
        self.type_cb = QComboBox(); self.type_cb.addItems(["Light", "Dark", "Flat", "Bias"])
        type_l.addWidget(QLabel("Typ:")); type_l.addWidget(self.type_cb); el.addLayout(type_l)

        iso_l = QHBoxLayout()
        self.iso_cb = QComboBox(); self.iso_cb.addItems(["100", "200", "400", "800", "1600", "3200", "6400", "12800"])
        self.iso_cb.setCurrentText("1600")
        iso_l.addWidget(QLabel("ISO:")); iso_l.addWidget(self.iso_cb); el.addLayout(iso_l)

        shut_l = QHBoxLayout()
        self.shut_cb = QComboBox(); self.shut_cb.addItems(["1/100", "1", "10", "30", "bulb"])
        self.shut_cb.setCurrentText("bulb")
        self.b_spin = QSpinBox(); self.b_spin.setRange(1, 7200); self.b_spin.setValue(300)
        shut_l.addWidget(QLabel("Čas:")); shut_l.addWidget(self.shut_cb); shut_l.addWidget(self.b_spin); el.addLayout(shut_l)
        
        self.app_b = QPushButton("Aplikovať ISO/Shutter"); self.app_b.clicked.connect(self.apply_settings)
        el.addWidget(self.app_b); exp_g.setLayout(el); mid.addWidget(exp_g)

        opt_g = QGroupBox("Astro Špeciál")
        ol = QVBoxLayout()
        self.mlu_check = QCheckBox("Mirror Lockup"); self.mlu_check.setChecked(True)
        self.lcd_check = QCheckBox("Vypnúť LCD (Heat reduction)"); self.lcd_check.setChecked(True)
        ol.addWidget(self.mlu_check); ol.addWidget(self.lcd_check)
        
        f_lay = QHBoxLayout()
        f_n = QPushButton("< Near"); f_f = QPushButton("Far >")
        f_n.clicked.connect(lambda: self.focus("Near 1")); f_f.clicked.connect(lambda: self.focus("Far 1"))
        f_lay.addWidget(f_n); f_lay.addWidget(f_f); ol.addLayout(f_lay)
        opt_g.setLayout(ol); mid.addWidget(opt_g)
        main.addLayout(mid)

        # --- Sekcia 4: Sekvencer ---
        cap_g = QGroupBox("Sekvencia snímania")
        cal = QHBoxLayout()
        self.frames_s = QSpinBox(); self.frames_s.setRange(1, 9999); self.frames_s.setValue(30)
        self.int_s = QSpinBox(); self.int_s.setValue(5)
        self.start_b = QPushButton("ŠTART"); self.start_b.setStyleSheet("background-color: #500; font-weight: bold;")
        self.start_b.clicked.connect(self.start_seq)
        self.stop_b = QPushButton("STOP"); self.stop_b.setEnabled(False); self.stop_b.clicked.connect(self.stop_seq)
        cal.addWidget(QLabel("Počet:")); cal.addWidget(self.frames_s); cal.addWidget(QLabel("Pauza (s):")); cal.addWidget(self.int_s)
        cal.addWidget(self.start_b); cal.addWidget(self.stop_b)
        cap_g.setLayout(cal); main.addWidget(cap_g)

        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setFont(QFont("Monospace", 9))
        main.addWidget(self.log)

    def apply_astro_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget, QDialog { background-color: #080808; color: #ff3333; font-family: 'Segoe UI', sans-serif; }
            QGroupBox { border: 1px solid #440000; border-radius: 4px; margin-top: 15px; font-weight: bold; }
            QPushButton { background-color: #1a1a1a; border: 1px solid #660000; color: #ff4444; padding: 5px; }
            QPushButton:hover { background-color: #400; }
            QLineEdit, QComboBox, QSpinBox, QTextEdit { background-color: #121212; border: 1px solid #330000; color: #ffaaaa; }
            QCheckBox { color: #ff6666; }
        """)

    def get_port(self): 
        return [f"--port=ptpip:{self.ip_in.text()}"] if self.wifi_r.isChecked() else []

    def detect(self): 
        self.run_cmd(["--auto-detect"])

    def focus(self, v): 
        self.run_cmd(["--set-config", f"manualfocusdrive={v}"])
    
    def apply_settings(self):
        # Rozdelíme príkazy na samostatné volania s pauzami pre stabilitu PTP
        self.log.append("--- Aplikujem nastavenia (stabilizovaný režim) ---")
        base = ["gphoto2"] + self.get_port()
        
        # ISO
        self.run_raw_cmd(base + ["--set-config", f"iso={self.iso_cb.currentText()}"])
        time.sleep(0.5)
        
        # Shutter
        if self.shut_cb.currentText() != "bulb": 
            self.run_raw_cmd(base + ["--set-config", f"shutterspeed={self.shut_cb.currentText()}"])
            time.sleep(0.5)
            
        # Astro doplnky - MLU môže zlyhať na niektorých FW, preto ignorujeme chybu
        if self.mlu_check.isChecked(): 
            self.run_raw_cmd(base + ["--set-config", "mirrorlockup=On"])
            time.sleep(0.5)
            
        if self.lcd_check.isChecked():
            self.run_raw_cmd(base + ["--set-config", "viewfinder=Off"])

    def run_raw_cmd(self, full_cmd_list):
        s = {'cmd': full_cmd_list}
        self.worker = GphotoWorker(self.get_port(), s, "single")
        self.worker.log_signal.connect(self.log.append)
        self.worker.start()

    def run_cmd(self, args):
        s = {'cmd': ["gphoto2"] + self.get_port() + args}
        self.worker = GphotoWorker(self.get_port(), s, "single")
        self.worker.log_signal.connect(self.log.append)
        self.worker.start()

    def start_seq(self):
        s = {
            'target': self.target_in.text(), 'pattern': self.pattern_in.text(),
            'type': self.type_cb.currentText(), 'iso': self.iso_cb.currentText(),
            'exp_label': self.b_spin.value() if self.shut_cb.currentText()=="bulb" else self.shut_cb.currentText(),
            'shutter_val': self.shut_cb.currentText(), 'bulb_time': self.b_spin.value(),
            'frames': self.frames_s.value(), 'interval': self.int_s.value()
        }
        self.worker = GphotoWorker(self.get_port(), s, "sequence")
        self.worker.log_signal.connect(self.log.append)
        self.worker.finished_signal.connect(lambda: self.set_ui(True))
        self.set_ui(False)
        self.worker.start()

    def stop_seq(self): 
        if self.worker: self.worker.stop()

    def set_ui(self, st): 
        self.start_b.setEnabled(st); self.stop_b.setEnabled(not st)

    def prompt_update(self, c):
        if QMessageBox.question(self, "OTA Update", "K dispozícii je nová verzia na GitHube. Aktualizovať?") == QMessageBox.StandardButton.Yes:
            try:
                with open(__file__, 'w', encoding='utf-8') as f: f.write(c)
                QMessageBox.information(self, "Hotovo", "Aktualizované. Reštartujte aplikáciu.")
                sys.exit()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodarilo sa aktualizovať: {e}")

    def show_help(self):
        QMessageBox.information(self, "Pattern & Astro Help", 
            "Zástupné znaky:\n%O - Objekt\n%T - Typ\n%N - Poradie\n%I - ISO\n%E - Čas (automaticky mení / na -)\n%D - Dátum\n%H - Čas\n\n"
            "WiFi TIP: Ak dostávate 'PTP Device Busy', zväčšite pauzu medzi snímkami.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DevControlApp()
    win.show()
    sys.exit(app.exec())
