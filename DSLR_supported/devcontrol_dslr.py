import sys
import subprocess
import time
import requests
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QSpinBox, 
                             QPushButton, QTextEdit, QGroupBox, QLineEdit, 
                             QRadioButton, QDialog, QScrollArea, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

# --- KONFIGURÁCIA AKTUALIZÁCIÍ (OTA) ---
GITHUB_RAW_URL = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/DSLR_supported/devcontrol_dslr.py"
CURRENT_VERSION = "2026.04_1.0" # Verzia tvojho lokálneho súboru

class UpdateWorker(QThread):
    update_available = pyqtSignal(str)
    no_update = pyqtSignal()

    def run(self):
        try:
            response = requests.get(GITHUB_RAW_URL, timeout=5)
            if response.status_code == 200:
                # Jednoduchá kontrola verzie v texte súboru (hľadá CURRENT_VERSION = "X.X.X")
                remote_content = response.text
                import re
                match = re.search(r'CURRENT_VERSION = "([\d.]+)"', remote_content)
                if match:
                    remote_version = match.group(1)
                    if remote_version != CURRENT_VERSION:
                        self.update_available.emit(remote_content)
                        return
            self.no_update.emit()
        except Exception:
            self.no_update.emit()

# --- PRACOVNÉ VLÁKNO PRE GPHOTO2 ---
class GphotoWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, port_arg, frames, interval, shutter, bulb_time, cmd_type="sequence"):
        super().__init__()
        self.port_arg = port_arg
        self.frames = frames
        self.interval = interval
        self.shutter = shutter
        self.bulb_time = bulb_time
        self.cmd_type = cmd_type
        self.single_cmd_args = []
        self.is_running = True

    def run(self):
        if self.cmd_type == "single_cmd":
            self.execute_command(self.single_cmd_args)
            self.finished_signal.emit(True)
            return

        self.log_signal.emit(f"--- ŠTART SEKVENCIE (Verzia {CURRENT_VERSION}) ---")
        for i in range(1, self.frames + 1):
            if not self.is_running:
                self.log_signal.emit("--- SEKVENCIA PRERUŠENÁ ---")
                break
                
            self.log_signal.emit(f"\nSnímka {i}/{self.frames}...")
            filename = f"devcontrol_6D_F{i}_%Y%m%d_%H%M%S.%C"
            
            if self.shutter == "bulb":
                cmd = ["gphoto2"] + self.port_arg + [
                    "--set-config", "bulb=1",
                    "--wait-event", f"{self.bulb_time}s",
                    "--set-config", "bulb=0",
                    "--wait-event-and-download", "5s",
                    "--filename", filename
                ]
            else:
                cmd = ["gphoto2"] + self.port_arg + [
                    "--capture-image-and-download",
                    "--filename", filename
                ]
                
            success = self.execute_command(cmd)
            if not success: break
            if i < self.frames and self.is_running:
                time.sleep(self.interval)
                
        self.finished_signal.emit(True)

    def execute_command(self, cmd):
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(process.stdout.readline, ''):
                if not self.is_running:
                    process.terminate()
                    return False
                self.log_signal.emit(line.strip())
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log_signal.emit(f"Chyba: {str(e)}")
            return False

    def stop(self):
        self.is_running = False

# --- POMOCNÍK ---
class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DevControl DSLR - Pomocník")
        self.resize(600, 450)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel("""
        <h2 style='color:#ff4444;'>DevControl DSLR Pomocník</h2>
        <b>Aktualizácie:</b> Program pri štarte kontroluje GitHub.<br><br>
        <b>BULB Režim:</b> Vyber 'bulb' v zozname. Nastav čas nad 30s. 
        Fotoaparát prepni na hornom koliesku do polohy 'B'.<br><br>
        <b>WiFi:</b> Zadaj IP fotoaparátu (PTP/IP).<br><br>
        <b>Focus:</b> Objektív musí byť na AF. Príkazy posúvajú motorček bez vibrácií.
        """)
        content.setWordWrap(True)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        btn = QPushButton("OK")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setStyleSheet(parent.styleSheet())

# --- HLAVNÉ OKNO ---
class DevControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"DevControl DSLR Controller v{CURRENT_VERSION}")
        self.resize(950, 750)
        self.worker = None
        self.setup_ui()
        self.apply_astro_theme()
        self.check_for_updates()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Connection & Update Info
        top = QHBoxLayout()
        conn_box = QGroupBox("Pripojenie")
        cl = QHBoxLayout()
        self.usb_radio = QRadioButton("USB")
        self.usb_radio.setChecked(True)
        self.wifi_radio = QRadioButton("WiFi")
        self.ip_in = QLineEdit("192.168.1.2")
        self.ip_in.setEnabled(False)
        self.wifi_radio.toggled.connect(lambda: self.ip_in.setEnabled(self.wifi_radio.isChecked()))
        self.det_btn = QPushButton("Detekovať")
        self.det_btn.clicked.connect(self.detect_camera)
        cl.addWidget(self.usb_radio); cl.addWidget(self.wifi_radio); cl.addWidget(self.ip_in); cl.addWidget(self.det_btn)
        conn_box.setLayout(cl)
        top.addWidget(conn_box, 4)
        
        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(lambda: HelpDialog(self).exec())
        top.addWidget(self.help_btn, 1)
        layout.addLayout(top)

        # Settings
        mid = QHBoxLayout()
        set_box = QGroupBox("Expozícia")
        sl = QVBoxLayout()
        
        # ISO & Shutter
        iso_l = QHBoxLayout()
        self.iso_cb = QComboBox()
        self.iso_cb.addItems(["100", "400", "800", "1600", "3200", "6400"])
        self.iso_cb.setCurrentText("800")
        iso_l.addWidget(QLabel("ISO:")); iso_l.addWidget(self.iso_cb)
        sl.addLayout(iso_l)

        shut_l = QHBoxLayout()
        self.shut_cb = QComboBox()
        self.shut_cb.addItems(["1/100", "1", "10", "30", "bulb"])
        self.shut_cb.setCurrentText("30")
        self.shut_cb.currentTextChanged.connect(self.toggle_bulb)
        self.b_spin = QSpinBox(); self.b_spin.setRange(31, 3600); self.b_spin.setEnabled(False)
        shut_l.addWidget(QLabel("Čas:")); shut_l.addWidget(self.shut_cb); shut_l.addWidget(QLabel("Bulb(s):")); shut_l.addWidget(self.b_spin)
        sl.addLayout(shut_l)
        
        self.app_btn = QPushButton("Aplikovať")
        self.app_btn.clicked.connect(self.apply_settings)
        sl.addWidget(self.app_btn)
        set_box.setLayout(sl)
        mid.addWidget(set_box)

        # Focus
        foc_box = QGroupBox("Ostrenie (AF prepínač zapnutý)")
        fl = QVBoxLayout()
        fl1 = QHBoxLayout(); fl2 = QHBoxLayout()
        self.f1 = QPushButton("<<< Far"); self.f2 = QPushButton("< Far")
        self.n1 = QPushButton("Near >"); self.n2 = QPushButton("Near >>>")
        self.f1.clicked.connect(lambda: self.run_single(["--set-config", "manualfocusdrive=Far 3"]))
        self.f2.clicked.connect(lambda: self.run_single(["--set-config", "manualfocusdrive=Far 1"]))
        self.n1.clicked.connect(lambda: self.run_single(["--set-config", "manualfocusdrive=Near 1"]))
        self.n2.clicked.connect(lambda: self.run_single(["--set-config", "manualfocusdrive=Near 3"]))
        fl1.addWidget(self.f1); fl1.addWidget(self.f2)
        fl2.addWidget(self.n1); fl2.addWidget(self.n2)
        fl.addLayout(fl1); fl.addLayout(fl2)
        foc_box.setLayout(fl)
        mid.addWidget(foc_box)
        layout.addLayout(mid)

        # Sequence
        seq_box = QGroupBox("Snímanie")
        seql = QHBoxLayout()
        self.f_spin = QSpinBox(); self.f_spin.setValue(10)
        self.i_spin = QSpinBox(); self.i_spin.setValue(2)
        self.start_btn = QPushButton("ŠTART"); self.start_btn.clicked.connect(self.start_sequence)
        self.stop_btn = QPushButton("STOP"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self.stop_sequence)
        seql.addWidget(QLabel("Snímky:")); seql.addWidget(self.f_spin); seql.addWidget(QLabel("Interval:")); seql.addWidget(self.i_spin)
        seql.addWidget(self.start_btn); seql.addWidget(self.stop_btn)
        seq_box.setLayout(seql)
        layout.addWidget(seq_box)

        self.log = QTextEdit(); self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def apply_astro_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget, QDialog { background-color: #0f0f0f; color: #ff3333; }
            QGroupBox { border: 1px solid #ff3333; border-radius: 4px; margin-top: 12px; font-weight: bold; }
            QPushButton { background-color: #222; border: 1px solid #ff3333; color: #ff3333; padding: 5px; }
            QPushButton:hover { background-color: #400; }
            QComboBox, QSpinBox, QLineEdit, QTextEdit { background-color: #1a1a1a; border: 1px solid #662222; color: #ff8888; }
        """)

    def check_for_updates(self):
        self.up_worker = UpdateWorker()
        self.up_worker.update_available.connect(self.prompt_update)
        self.up_worker.start()

    def prompt_update(self, content):
        reply = QMessageBox.question(self, "Aktualizácia", "Nová verzia devcontrol_dslr je dostupná na GitHube. Aktualizovať?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(__file__, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "Hotovo", "Program bol aktualizovaný. Reštartujte ho prosím.")
                sys.exit()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodarilo sa zapísať súbor: {e}")

    def toggle_bulb(self, val):
        self.b_spin.setEnabled(val == "bulb")

    def run_single(self, args):
        if self.worker and self.worker.isRunning(): return
        self.worker = GphotoWorker(self.get_port(), 0, 0, "", 0, "single_cmd")
        self.worker.single_cmd_args = ["gphoto2"] + self.get_port() + args
        self.worker.log_signal.connect(self.log.append)
        self.worker.start()

    def get_port(self):
        return ["--port", f"ptpip:{self.ip_in.text()}"] if self.wifi_radio.isChecked() else []

    def detect_camera(self): self.run_single(["--auto-detect"])

    def apply_settings(self):
        args = ["--set-config", f"iso={self.iso_cb.currentText()}"]
        if self.shut_cb.currentText() != "bulb":
            args.extend(["--set-config", f"shutterspeed={self.shut_cb.currentText()}"])
        self.run_single(args)

    def start_sequence(self):
        self.worker = GphotoWorker(self.get_port(), self.f_spin.value(), self.i_spin.value(), self.shut_cb.currentText(), self.b_spin.value())
        self.worker.log_signal.connect(self.log.append)
        self.worker.finished_signal.connect(lambda: self.set_ui(True))
        self.set_ui(False)
        self.worker.start()

    def stop_sequence(self):
        if self.worker: self.worker.stop()

    def set_ui(self, state):
        self.start_btn.setEnabled(state); self.stop_btn.setEnabled(not state)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DevControlApp()
    window.show()
    sys.exit(app.exec())
