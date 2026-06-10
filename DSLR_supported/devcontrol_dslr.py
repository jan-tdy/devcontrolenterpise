import re
import sys
import subprocess
import time
import requests
import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QTextEdit, QGroupBox, QLineEdit,
    QRadioButton, QMessageBox, QCheckBox,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

# TODO: update GITHUB_RAW_URL after this project moves to its own repository
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main"
    "/DSLR_supported/devcontrol_dslr.py"
)
CURRENT_VERSION = "2026.4_1.3"


class UpdateWorker(QThread):
    update_available = pyqtSignal(str)

    def run(self):
        try:
            res = requests.get(GITHUB_RAW_URL, timeout=5)
            if res.status_code == 200:
                match = re.search(r'CURRENT_VERSION\s*=\s*"([\d._]+)"', res.text)
                if match and match.group(1) != CURRENT_VERSION:
                    self.update_available.emit(res.text)
        except Exception:
            pass


class ApplySettingsWorker(QThread):
    """Runs ISO/shutter/MLU/LCD gphoto2 commands off the main thread."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, cmds):
        super().__init__()
        self.cmds = cmds  # list of (cmd_list, delay_after_seconds)

    def run(self):
        for cmd, delay in self.cmds:
            self.log_signal.emit(f"> {' '.join(cmd)}")
            try:
                p = subprocess.run(cmd, capture_output=True, text=True)
                out = (p.stdout + p.stderr).strip()
                if out:
                    self.log_signal.emit(out)
            except Exception as e:
                self.log_signal.emit(f"Error: {e}")
            if delay:
                time.sleep(delay)
        self.finished_signal.emit()


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

        self.log_signal.emit(f"--- START ASTRO SEQUENCE v{CURRENT_VERSION} ---")

        # Set RAW format before sequence starts
        self.execute(["gphoto2"] + self.port + ["--set-config", "imageformat=RAW"])
        time.sleep(1)

        success = True
        for i in range(1, self.s['frames'] + 1):
            if not self.is_running:
                break

            now = datetime.datetime.now()
            fn = self.s['pattern']
            fn = fn.replace("%O", self.s['target'])
            fn = fn.replace("%T", self.s['type'])
            fn = fn.replace("%N", str(i).zfill(3))
            fn = fn.replace("%I", self.s['iso'])
            exp_clean = str(self.s['exp_label']).replace("/", "-")
            fn = fn.replace("%E", exp_clean)
            fn = fn.replace("%D", now.strftime("%Y%m%d"))
            fn = fn.replace("%H", now.strftime("%H%M%S"))
            fn = re.sub(r'[\\/*?:"<>|]', "", fn)

            self.log_signal.emit(f"\nFrame {i}/{self.s['frames']} -> {fn}.CR2")

            if self.s['shutter_val'] == "bulb":
                cmd = ["gphoto2"] + self.port + [
                    "--bulb", str(self.s['bulb_time']),
                    "--capture-image-and-download",
                    "--filename", f"{fn}.CR2",
                ]
            else:
                cmd = ["gphoto2"] + self.port + [
                    "--capture-image-and-download",
                    "--filename", f"{fn}.CR2",
                ]

            if not self.execute(cmd):
                self.log_signal.emit("Communication error. Waiting 3 s before retry…")
                time.sleep(3)
                if not self.execute(cmd):
                    self.log_signal.emit("Critical connection error. Aborting sequence.")
                    success = False
                    break

            if i < self.s['frames'] and self.is_running:
                self.log_signal.emit(f"Interval: {self.s['interval']} s")
                time.sleep(self.s['interval'])

        self.finished_signal.emit(success)

    def execute(self, cmd):
        self.log_signal.emit(f"> {' '.join(cmd)}")
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in iter(p.stdout.readline, ''):
                if not self.is_running:
                    p.terminate()
                    p.wait()  # reap process to avoid zombie
                    return False
                self.log_signal.emit(line.strip())
            p.wait()
            return p.returncode == 0
        except Exception as e:
            self.log_signal.emit(f"System error: {e}")
            return False

    def stop(self):
        self.is_running = False


class DevControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"devcontrol_dslr v{CURRENT_VERSION}")
        self.resize(1100, 850)
        self.seq_worker = None
        self.cmd_worker = None
        self.apply_worker = None
        self.setup_ui()
        self.apply_astro_theme()

        self.up_worker = UpdateWorker()
        self.up_worker.update_available.connect(self.prompt_update)
        self.up_worker.start()

    def setup_ui(self):
        c = QWidget()
        self.setCentralWidget(c)
        main = QVBoxLayout(c)

        # Connection
        top = QHBoxLayout()
        conn_g = QGroupBox("Connection (Canon 6D)")
        cl = QHBoxLayout()
        self.usb_r = QRadioButton("USB")
        self.usb_r.setChecked(True)
        self.wifi_r = QRadioButton("WiFi (PTP/IP)")
        self.ip_in = QLineEdit("192.168.5.204")
        self.ip_in.setEnabled(False)
        self.wifi_r.toggled.connect(lambda: self.ip_in.setEnabled(self.wifi_r.isChecked()))
        self.det_b = QPushButton("Test Connection")
        self.det_b.clicked.connect(self.detect)
        cl.addWidget(self.usb_r)
        cl.addWidget(self.wifi_r)
        cl.addWidget(QLabel("IP:"))
        cl.addWidget(self.ip_in)
        cl.addWidget(self.det_b)
        conn_g.setLayout(cl)
        top.addWidget(conn_g, 4)
        self.help_b = QPushButton("Help / Tags")
        self.help_b.clicked.connect(self.show_help)
        top.addWidget(self.help_b, 1)
        main.addLayout(top)

        # File naming
        fn_g = QGroupBox("File Naming (Pattern)")
        fnl = QHBoxLayout()
        self.target_in = QLineEdit("IFN_Project")
        self.pattern_in = QLineEdit("%O_%T_S%N_ISO%I_%E")
        fnl.addWidget(QLabel("Object:"))
        fnl.addWidget(self.target_in)
        fnl.addWidget(QLabel("Pattern:"))
        fnl.addWidget(self.pattern_in)
        fn_g.setLayout(fnl)
        main.addWidget(fn_g)

        # Parameters
        mid = QHBoxLayout()

        exp_g = QGroupBox("Exposure")
        el = QVBoxLayout()
        type_l = QHBoxLayout()
        self.type_cb = QComboBox()
        self.type_cb.addItems(["Light", "Dark", "Flat", "Bias"])
        type_l.addWidget(QLabel("Type:"))
        type_l.addWidget(self.type_cb)
        el.addLayout(type_l)
        iso_l = QHBoxLayout()
        self.iso_cb = QComboBox()
        self.iso_cb.addItems(["100", "200", "400", "800", "1600", "3200", "6400", "12800"])
        self.iso_cb.setCurrentText("1600")
        iso_l.addWidget(QLabel("ISO:"))
        iso_l.addWidget(self.iso_cb)
        el.addLayout(iso_l)
        shut_l = QHBoxLayout()
        self.shut_cb = QComboBox()
        self.shut_cb.addItems(["1/100", "1", "10", "30", "bulb"])
        self.shut_cb.setCurrentText("bulb")
        self.b_spin = QSpinBox()
        self.b_spin.setRange(1, 7200)
        self.b_spin.setValue(300)
        shut_l.addWidget(QLabel("Time:"))
        shut_l.addWidget(self.shut_cb)
        shut_l.addWidget(self.b_spin)
        el.addLayout(shut_l)
        self.app_b = QPushButton("Apply ISO / Shutter")
        self.app_b.clicked.connect(self.apply_settings)
        el.addWidget(self.app_b)
        exp_g.setLayout(el)
        mid.addWidget(exp_g)

        opt_g = QGroupBox("Astro Special")
        ol = QVBoxLayout()
        self.mlu_check = QCheckBox("Mirror Lockup")
        self.mlu_check.setChecked(True)
        self.lcd_check = QCheckBox("Disable LCD (heat reduction)")
        self.lcd_check.setChecked(True)
        ol.addWidget(self.mlu_check)
        ol.addWidget(self.lcd_check)
        f_lay = QHBoxLayout()
        f_n = QPushButton("< Near")
        f_f = QPushButton("Far >")
        f_n.clicked.connect(lambda: self.focus("Near 1"))
        f_f.clicked.connect(lambda: self.focus("Far 1"))
        f_lay.addWidget(f_n)
        f_lay.addWidget(f_f)
        ol.addLayout(f_lay)
        opt_g.setLayout(ol)
        mid.addWidget(opt_g)
        main.addLayout(mid)

        # Sequencer
        cap_g = QGroupBox("Imaging Sequence")
        cal = QHBoxLayout()
        self.frames_s = QSpinBox()
        self.frames_s.setRange(1, 9999)
        self.frames_s.setValue(30)
        self.int_s = QSpinBox()
        self.int_s.setValue(5)
        self.start_b = QPushButton("START")
        self.start_b.setStyleSheet("background-color: #500; font-weight: bold;")
        self.start_b.clicked.connect(self.start_seq)
        self.stop_b = QPushButton("STOP")
        self.stop_b.setEnabled(False)
        self.stop_b.clicked.connect(self.stop_seq)
        cal.addWidget(QLabel("Frames:"))
        cal.addWidget(self.frames_s)
        cal.addWidget(QLabel("Interval (s):"))
        cal.addWidget(self.int_s)
        cal.addWidget(self.start_b)
        cal.addWidget(self.stop_b)
        cap_g.setLayout(cal)
        main.addWidget(cap_g)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Monospace", 9))
        main.addWidget(self.log)

    def apply_astro_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget, QDialog {
                background-color: #080808;
                color: #ff3333;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                border: 1px solid #440000;
                border-radius: 4px;
                margin-top: 15px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #660000;
                color: #ff4444;
                padding: 5px;
            }
            QPushButton:hover { background-color: #400; }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #121212;
                border: 1px solid #330000;
                color: #ffaaaa;
            }
            QCheckBox { color: #ff6666; }
        """)

    def get_port(self):
        return [f"--port=ptpip:{self.ip_in.text()}"] if self.wifi_r.isChecked() else []

    def detect(self):
        self._run_cmd_single(["--auto-detect"])

    def focus(self, v):
        self._run_cmd_single(["--set-config", f"manualfocusdrive={v}"])

    def apply_settings(self):
        self.log.append("--- Applying settings ---")
        base = ["gphoto2"] + self.get_port()
        cmds = [(base + ["--set-config", f"iso={self.iso_cb.currentText()}"], 0.5)]
        if self.shut_cb.currentText() != "bulb":
            cmds.append(
                (base + ["--set-config", f"shutterspeed={self.shut_cb.currentText()}"], 0.5)
            )
        if self.mlu_check.isChecked():
            cmds.append((base + ["--set-config", "mirrorlockup=On"], 0.5))
        if self.lcd_check.isChecked():
            cmds.append((base + ["--set-config", "viewfinder=Off"], 0.0))

        self.app_b.setEnabled(False)
        self.apply_worker = ApplySettingsWorker(cmds)
        self.apply_worker.log_signal.connect(self.log.append)
        self.apply_worker.finished_signal.connect(lambda: self.app_b.setEnabled(True))
        self.apply_worker.start()

    def _run_cmd_single(self, args):
        if self.cmd_worker and self.cmd_worker.isRunning():
            return
        s = {'cmd': ["gphoto2"] + self.get_port() + args}
        self.cmd_worker = GphotoWorker(self.get_port(), s, "single")
        self.cmd_worker.log_signal.connect(self.log.append)
        self.cmd_worker.start()

    def start_seq(self):
        if self.seq_worker and self.seq_worker.isRunning():
            return
        s = {
            'target':      self.target_in.text(),
            'pattern':     self.pattern_in.text(),
            'type':        self.type_cb.currentText(),
            'iso':         self.iso_cb.currentText(),
            'exp_label':   self.b_spin.value() if self.shut_cb.currentText() == "bulb"
                           else self.shut_cb.currentText(),
            'shutter_val': self.shut_cb.currentText(),
            'bulb_time':   self.b_spin.value(),
            'frames':      self.frames_s.value(),
            'interval':    self.int_s.value(),
        }
        self.seq_worker = GphotoWorker(self.get_port(), s, "sequence")
        self.seq_worker.log_signal.connect(self.log.append)
        self.seq_worker.finished_signal.connect(self.set_ui)
        self.set_ui(False)
        self.seq_worker.start()

    def stop_seq(self):
        if self.seq_worker:
            self.seq_worker.stop()

    def set_ui(self, enabled):
        self.start_b.setEnabled(bool(enabled))
        self.stop_b.setEnabled(not bool(enabled))

    def prompt_update(self, new_code: str):
        # SECURITY: downloaded code is written directly to __file__ with no signature
        # verification. Only accept from your own trusted repository over HTTPS.
        if QMessageBox.question(
            self,
            "OTA Update",
            "A new version is available on GitHub. Update now?",
        ) == QMessageBox.StandardButton.Yes:
            try:
                Path(__file__).resolve().write_text(new_code, encoding="utf-8")
                QMessageBox.information(
                    self, "Done", "Updated. Please restart the application."
                )
                sys.exit(0)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Update failed: {e}")

    def show_help(self):
        QMessageBox.information(
            self,
            "Pattern & Astro Help",
            "Pattern wildcards:\n"
            "%O  – Target object name\n"
            "%T  – Frame type (Light/Dark/Flat/Bias)\n"
            "%N  – Sequence number (001, 002, …)\n"
            "%I  – ISO value\n"
            "%E  – Exposure time (/ replaced by - automatically)\n"
            "%D  – Date (YYYYMMDD)\n"
            "%H  – Time (HHMMSS)\n\n"
            "WiFi tip: If you see 'PTP Device Busy', increase the interval between frames.",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DevControlApp()
    win.show()
    sys.exit(app.exec())
