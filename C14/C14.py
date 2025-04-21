# Licensed under the JADIV Private License v1.0 – see LICENSE file for details.
import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime, timedelta
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

        self.timer_kill = QtCore.QTimer()
        self.timer_kill.timeout.connect(self.skontroluj_a_killni_ccdciel_indi)
        self.timer_kill.start(60 * 1000)  # každú minútu

    def skontroluj_a_killni_ccdciel_indi(self):
        teraz = datetime.now()
        je_utorok = teraz.weekday() == 1
        je_stvrtok = teraz.weekday() == 3
        treti_stvrtok = (teraz.day - 1) // 7 == 2
        je_cas = teraz.hour == 1 and teraz.minute == 26

        if je_cas and (je_utorok or (je_stvrtok and treti_stvrtok)):
            try:
                subprocess.run("pkill -f ccdciel", shell=True)
                subprocess.run("pkill -f indi", shell=True)
            except Exception as e:
                pass

    # (zvyšok triedy zostáva nezmenený)

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
                subprocess.run(
                    f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py -o {PROGRAM_CESTA}",
                    shell=True, check=True)
                QtWidgets.QMessageBox.information(bug_window, "Hotovo", "Program bol aktualizovaný. Spusť ho znova.")
                bug_window.close()
            except Exception as ex:
                QtWidgets.QMessageBox.critical(bug_window, "Chyba", f"Zlyhala aktualizácia: {ex}")
        btn_update = QtWidgets.QPushButton("Aktualizovať program")
        btn_update.clicked.connect(spusti_update)
        layout.addWidget(btn_update)
        bug_window.show()
    sys.exit(app.exec_())
