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
CURRENT_VERSION = "2026.04_1.1" 

class UpdateWorker(QThread):
    update_available = pyqtSignal(str)
    def run(self):
        try:
            res = requests.get(GITHUB_RAW_URL, timeout=5)
            if res.status_code == 200:
                match = re.search(r'CURRENT_VERSION = "([\d.]+)"', res.text)
                if match and match.group(1) != CURRENT_VERSION:
                    self.update_available.emit(res.text)
        except: pass

class GphotoWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, port, settings, cmd_type="sequence"):
        super().__init__()
        self.port = port
        self.s = settings
        self.cmd_type = cmd_type
        self.is_running = True

    def run(self):
        if self.cmd_type == "single":
            self.execute(self.s['cmd'])
            self.finished_signal.emit(True)
            return

        self.log_signal.emit(f"--- ŠTART ASTRO SEKVENCIE v{CURRENT_VERSION} ---")
        self.execute(["gphoto2"] + self.port + ["--set-config", "imageformat=RAW"])
        
        for i in range(1, self.s['frames'] + 1):
            if not self.is_running: break
            
            # Generovanie názvu podľa vzoru
            now = datetime.datetime.now()
            fn = self.s['pattern']
            fn = fn.replace("%O", self.s['target'])
            fn = fn.replace("%T", self.s['type'])
            fn = fn.replace("%N", str(i).zfill(3))
            fn = fn.replace("%I", self.s['iso'])
            fn = fn.replace("%E", str(self.s['exp_label']))
            fn = fn.replace("%D", now.strftime("%Y%m%d"))
            fn = fn.replace("%H", now.strftime("%H%M%S"))
            
            self.log_signal.emit(f"\nSnímka {i}/{self.s['frames']} -> {fn}.CR2")

            if self.s['shutter_val'] == "bulb":
                cmd = ["gphoto2"] + self.port + [
                    "--set-config", "bulb=1",
                    "--wait-event", f"{self.s['bulb_time']}s",
                    "--set-config", "bulb=0",
                    "--wait-event-and-download", "2s",
                    "--filename", f"{fn}.CR2"
                ]
            else:
                cmd = ["gphoto2"] + self.port + [
                    "--capture-image-and-download",
                    "--filename", f"{fn}.CR2"
                ]
            
            if not self.execute(cmd): break
            if i < self.s['frames'] and self.is_running:
                time.sleep(self.s['interval'])
                
        self.finished_signal.emit(True)

    def execute(self, cmd):
        self.log_signal.emit(f"> {' '.join(cmd)}")
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(p.stdout.readline, ''):
                if not self.is_running: p.terminate(); return False
                self.log_signal.emit(line.strip())
            p.wait(); return p.returncode == 0
        except Exception as e:
            self.log_signal.emit(f"Chyba: {e}"); return False

    def stop(self): self.is_running = False

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
        self.ip_in = QLineEdit("192.168.1.100"); self.ip_in.setEnabled(False)
        self.wifi_r.toggled.connect(lambda: self.ip_in.setEnabled(self.wifi_r.isChecked()))
        self.det_b = QPushButton("Detekovať"); self.det_b.clicked.connect(self.detect)
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
        self.iso_cb = QComboBox(); self.iso_cb.addItems(["800", "1600", "3200", "6400", "12800"])
        iso_l.addWidget(QLabel("ISO:")); iso_l.addWidget(self.iso_cb); el.addLayout(iso_l)

        shut_l = QHBoxLayout()
        self.shut_cb = QComboBox(); self.shut_cb.addItems(["10", "30", "bulb"])
        self.b_spin = QSpinBox(); self.b_spin.setRange(1, 7200); self.b_spin.setValue(300)
        shut_l.addWidget(QLabel("Čas:")); shut_l.addWidget(self.shut_cb); shut_l.addWidget(self.b_spin); el.addLayout(shut_l)
        
        self.app_b = QPushButton("Aplikovať nastavenia"); self.app_b.clicked.connect(self.apply_settings)
        el.addWidget(self.app_b); exp_g.setLayout(el); mid.addWidget(exp_g)

        opt_g = QGroupBox("Optika & Iné")
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
        cap_g = QGroupBox("Snímanie")
        cal = QHBoxLayout()
        self.frames_s = QSpinBox(); self.frames_s.setRange(1, 9999); self.frames_s.setValue(30)
        self.int_s = QSpinBox(); self.int_s.setValue(5)
        self.start_b = QPushButton("ŠTART"); self.start_b.setStyleSheet("background-color: #500;")
        self.start_b.clicked.connect(self.start_seq)
        self.stop_b = QPushButton("STOP"); self.stop_b.setEnabled(False); self.stop_b.clicked.connect(self.stop_seq)
        cal.addWidget(QLabel("Počet:")); cal.addWidget(self.frames_s); cal.addWidget(QLabel("Pauza (s):")); cal.addWidget(self.int_s)
        cal.addWidget(self.start_b); cal.addWidget(self.stop_b)
        cap_g.setLayout(cal); main.addWidget(cap_g)

        self.log = QTextEdit(); self.log.setReadOnly(True); main.addWidget(self.log)

    def apply_astro_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget, QDialog { background-color: #0a0a0a; color: #ff3333; font-family: 'Segoe UI', Arial; }
            QGroupBox { border: 1px solid #330000; border-radius: 4px; margin-top: 15px; font-weight: bold; }
            QPushButton { background-color: #1a1a1a; border: 1px solid #550000; color: #ff4444; padding: 5px; }
            QPushButton:hover { background-color: #300; }
            QLineEdit, QComboBox, QSpinBox, QTextEdit { background-color: #111; border: 1px solid #220000; color: #ff9999; }
        """)

    def get_port(self): return ["--port", f"ptpip:{self.ip_in.text()}"] if self.wifi_r.isChecked() else []
    def detect(self): self.run_cmd(["--auto-detect"])
    def focus(self, v): self.run_cmd(["--set-config", f"manualfocusdrive={v}"])
    
    def apply_settings(self):
        c = ["--set-config", f"iso={self.iso_cb.currentText()}"]
        if self.shut_cb.currentText() != "bulb": c.extend(["--set-config", f"shutterspeed={self.shut_cb.currentText()}"])
        if self.mlu_check.isChecked(): c.extend(["--set-config", "mirrorlockup=On"])
        self.run_cmd(c)

    def run_cmd(self, args):
        s = {'cmd': ["gphoto2"] + self.get_port() + args}
        self.worker = GphotoWorker(self.get_port(), s, "single")
        self.worker.log_signal.connect(self.log.append); self.worker.start()

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
        self.set_ui(False); self.worker.start()

    def stop_seq(self): 
        if self.worker: self.worker.stop()
    def set_ui(self, st): self.start_b.setEnabled(st); self.stop_b.setEnabled(not st)

    def prompt_update(self, c):
        if QMessageBox.question(self, "Update", "Aktualizovať?") == QMessageBox.StandardButton.Yes:
            with open(__file__, 'w') as f: f.write(c)
            sys.exit()

    def show_help(self):
        QMessageBox.information(self, "Pattern Help", 
            "Zástupné znaky pre názov:\n%O - Objekt\n%T - Typ (Light/Dark...)\n%N - Číslo snímky\n%I - ISO\n%E - Expozícia\n%D - Dátum\n%H - Čas")

if __name__ == "__main__":
    app = QApplication(sys.argv); win = DevControlApp(); win.show(); sys.exit(app.exec())
