# Licensed under the JADIV Private License v1.0 – see LICENSE file for details.
import sys
import subprocess
import time
import threading
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime
import pytz
import os

ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
SSH_USER = "dpv"
SSH_PASS = "otj0711"
CENTRAL2_IP = "172.20.20.133"
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"
SSH_PASS2 = "otj0711"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14")
        self.resize(1280, 720)
        self.setMinimumSize(1024, 600)

        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #212121;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 9.5pt;
            }
            QPushButton {
                background-color: #d4e157;
                color: #212121;
                border: none;
                border-radius: 10px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c0ca33;
            }
            QPushButton:pressed {
                background-color: #afb42b;
            }
            QTextEdit#logBox {
                background-color: #f9fbe7;
                color: #33691e;
                border: 1px solid #cddc39;
                border-radius: 10px;
                padding: 8px;
                font-size: 9pt;
            }
            QGroupBox {
                background-color: #f1f8e9;
                border: 2px solid #cddc39;
                border-radius: 14px;
                padding: 12px;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 9.5pt;
                color: #558b2f;
            }
            QLabel {
                color: #212121;
                font-weight: 500;
                font-size: 9.5pt;
            }
            QLineEdit, QComboBox, QTextEdit, QCheckBox {
                background-color: #ffffff;
                border: 1px solid #cddc39;
                border-radius: 8px;
                padding: 6px;
                font-size: 9pt;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #aeea00;
            }
            QCheckBox {
                spacing: 6px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #f1f8e9;
                border-radius: 5px;
                width: 8px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #cddc39;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #afb42b;
            }
            QToolTip {
                background-color: #d4e157;
                color: black;
                border: 1px solid #cddc39;
                padding: 6px;
                border-radius: 5px;
                font-size: 9pt;
            }
        """)

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        self.setCentralWidget(widget)

        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(120)
        layout.addWidget(self.log_box)

        self.log_file_path = "/home/dpv/j44softapps-socketcontrol/log.txt"
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, "r") as f:
                self.log_box.setPlainText(f.read())

        self.status_labels = {}
        for name in ZASUVKY:
            label = QtWidgets.QLabel(f"{name}: ")
            status = QtWidgets.QLabel()
            status.setPixmap(QtGui.QPixmap("led_def.png"))
            self.status_labels[name] = status
            layout.addWidget(label)
            layout.addWidget(status)

        self.aktualizuj_stav_zasuviek()
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)
        self.status_timer.start(5 * 60 * 1000)

        self.kill_timer = QtCore.QTimer()
        self.kill_timer.timeout.connect(self.auto_kill_processes)
        self.kill_timer.start(60 * 1000)

    def auto_kill_processes(self):
        now = datetime.now()
        weekday = now.weekday()
        if now.hour == 1 and now.minute == 26 and (weekday == 1 or (weekday == 3 and 15 <= now.day <= 21)):
            try:
                subprocess.run("pkill -f ccdciel", shell=True)
                subprocess.run("pkill -f indi", shell=True)
            except:
                pass

    def aktualizuj_stav_zasuviek(self):
        self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aktualizujem stav zásuviek.")
        for n, c in ZASUVKY.items():
            self.zisti_stav_zasuvky(c, n)

    def zisti_stav_zasuvky(self, cis, lab):
        try:
            out = subprocess.check_output(f"sispmctl -nqg {cis}", shell=True, text=True).strip()
            pix = "led_green.png" if out == "1" else "led_red.png" if out == "0" else "led_def.png"
            self.status_labels[lab].setPixmap(QtGui.QPixmap(pix))
        except:
            self.status_labels[lab].setPixmap(QtGui.QPixmap("led_def.png"))

    def loguj(self, msg, typ="info"):
        if "Aktualizujem stav zásuviek" in msg:
            return
        t = QtCore.QTime.currentTime().toString()
        full_msg = f"[{t}] {msg}"
        self.log_box.append(full_msg)
        self.log_box.moveCursor(QtGui.QTextCursor.End)
        try:
            with open(self.log_file_path, "a") as f:
                f.write(full_msg + "\n")
        except Exception as e:
            print("Chyba pri ukladaní logu:", e)

    def aktualizuj_program(self):
        try:
            subprocess.run(f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py -o {PROGRAM_CESTA}", shell=True, check=True)
            self.loguj("Program bol úspešne aktualizovaný. Reštartujem.", "success")
            subprocess.Popen([sys.executable, PROGRAM_CESTA])
            sys.exit(0)
        except Exception as e:
            self.loguj(f"Chyba pri aktualizácii! {e}", "error")

    def ovladaj_strechu(self, s):
        if s == "sever":
            p1, p2 = "crelay -s BITFT 2 ON", "crelay -s BITFT 2 OFF"
        elif s == "juh":
            p1, p2 = "crelay -s BITFT 1 ON", "crelay -s BITFT 1 OFF"
        elif s == "both":
            try:
                subprocess.run("crelay -s BITFT 1 ON", shell=True, check=True)
                subprocess.run("crelay -s BITFT 2 ON", shell=True, check=True)
                time.sleep(2)
                subprocess.run("crelay -s BITFT 1 OFF", shell=True, check=True)
                subprocess.run("crelay -s BITFT 2 OFF", shell=True, check=True)
                return
            except:
                self.loguj(f"Chyba strecha {s}")
                return
        else:
            return
        try:
            subprocess.run(p1, shell=True, check=True)
            time.sleep(2)
            subprocess.run(p2, shell=True, check=True)
        except:
            self.loguj(f"Chyba strecha {s}")

    def spusti_indistarter_c14(self):
        try:
            out = subprocess.check_output("indistarter", shell=True)
            self.loguj(out.decode())
        except:
            self.loguj("Chyba spustenia INDISTARTER C14")

    def spusti_indistarter_az2000(self):
        try:
            out = subprocess.check_output(f"ssh {SSH_USER2}@{AZ2000_IP} indistarter", shell=True)
            self.loguj(out.decode())
        except:
            self.loguj("Chyba INDISTARTER AZ2000")

    def wake_on_lan(self, mac):
        try:
            send_magic_packet(mac)
            self.loguj(f"WOL na {mac}")
        except:
            self.loguj("Chyba WOL")

class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        pix = QtGui.QPixmap("logo.png")
        super().__init__(pix)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QSplashScreen {
                background-color: black;
            }
            QLabel {
                color: lime;
                font-family: Consolas;
            }
            QProgressBar {
                border: 2px solid #00ff00;
                border-radius: 5px;
                background-color: #111;
            }
            QProgressBar::chunk {
                background-color: lime;
                width: 10px;
            }
        """)
        lic = QtWidgets.QLabel("Licensed under the JADIV Private License v1.0 – see LICENSE file for details.", self)
        lic.setAlignment(QtCore.Qt.AlignCenter)
        lic.setGeometry(0, pix.height(), pix.width(), 20)
        lbl = QtWidgets.QLabel("Jadiv DEVCONTROL Enterprise for Vihorlat Observatory", self)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setGeometry(0, pix.height() + 20, pix.width(), 40)
        pr = QtWidgets.QProgressBar(self)
        pr.setGeometry(10, pix.height() + 70, pix.width() - 20, 20)
        pr.setRange(0, 100)
        pr.setValue(0)
        pr.setTextVisible(False)
        self.pr = pr
        self.resize(pix.width(), pix.height() + 100)

    def simulate_loading(self):
        for i in range(101):
            self.pr.setValue(i)
            QtWidgets.qApp.processEvents()
            time.sleep(0.010)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    QtWidgets.qApp.processEvents()
    splash.simulate_loading()
    try:
        window = MainWindow()
        window.show()
        splash.finish(window)
    except Exception as e:
        splash.close()
        bug_window = QtWidgets.QWidget()
        bug_window.setWindowTitle("SPLASH BUG – Chyba pri štarte hlavného okna")
        bug_window.setMinimumSize(500, 200)
        layout = QtWidgets.QVBoxLayout(bug_window)
        error_label = QtWidgets.QLabel("Nastal problém pri štarte hlavného okna aplikácie.\nPravdepodobne je chyba v aktualizovanom kóde.\n")
        error_label.setStyleSheet("color: red; font-size: 11pt; font-weight: bold;")
        layout.addWidget(error_label)
        error_details = QtWidgets.QTextEdit()
        error_details.setReadOnly(True)
        error_details.setPlainText(str(e))
        layout.addWidget(error_details)
        def spusti_update():
            try:
                subprocess.run(f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py -o {PROGRAM_CESTA}", shell=True, check=True)
                QtWidgets.QMessageBox.information(bug_window, "Hotovo", "Program bol aktualizovaný. Spusť ho znova.")
                bug_window.close()
            except Exception as ex:
                QtWidgets.QMessageBox.critical(bug_window, "Chyba", f"Zlyhala aktualizácia: {ex}")
        def nainstaluj_zavislosti():
            try:
                subprocess.run("pip install pyqt5 wakeonlan pytz", shell=True)
                QtWidgets.QMessageBox.information(bug_window, "OK", "Závislosti boli nainštalované.")
            except Exception as ex:
                QtWidgets.QMessageBox.critical(bug_window, "Chyba", f"Zlyhala inštalácia závislostí: {ex}")
        btn_update = QtWidgets.QPushButton("Aktualizovať program")
        btn_update.clicked.connect(spusti_update)
        layout.addWidget(btn_update)
        btn_install = QtWidgets.QPushButton("Nainštalovať závislosti")
        btn_install.clicked.connect(nainstaluj_zavislosti)
        layout.addWidget(btn_install)
        bug_window.show()
    sys.exit(app.exec_())
