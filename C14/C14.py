# Licensed under the JADIV Private License v1.0 – see LICENSE file for details.
import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime
import pytz

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
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - Version 25-3-2025 02")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.status_labels = {}

        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)
        self.grid_layout.addWidget(self.log_box, 99, 0, 1, 2)

        self.init_atacama_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()

        self.aktualizuj_stav_zasuviek()
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)
        self.status_timer.start(5 * 60 * 1000)

    def aktualizuj_stav_zasuviek(self):
        self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aktualizujem stav zásuviek.")
        for name, cislo in ZASUVKY.items():
            self.zisti_stav_zasuvky(cislo, name)

    def zisti_stav_zasuvky(self, cislo_zasuvky, label_name):
        try:
            prikaz_stav = f"sispmctl -nqg {cislo_zasuvky}"
            vystup_stav = subprocess.check_output(prikaz_stav, shell=True, text=True).strip()
            if vystup_stav == "1":
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_green.png"))
            elif vystup_stav == "0":
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_red.png"))
            else:
                self.loguj(f"Neočakávaný výstup pre stav zásuvky {cislo_zasuvky}: '{vystup_stav}'")
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri zisťovaní stavu zásuvky {cislo_zasuvky}: {e}")
            self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))
        except FileNotFoundError:
            self.loguj("Príkaz 'sispmctl' nebol nájdený. Nie je možné zistiť stav zásuviek.")
            for name in ZASUVKY:
                self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))

    def aktualizuj_program(self):
        try:
            self.loguj("Aktualizujem program...")
            prikaz_stiahnutie = f"curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/refs/heads/main/C14/C14.py"
            subprocess.run(prikaz_stiahnutie, shell=True, check=True)

            prikaz_nahradenie = f"cp C14.py {PROGRAM_CESTA}"
            subprocess.run(prikaz_nahradenie, shell=True, check=True)

            self.loguj("Program bol aktualizovaný. Zavrite toto okno a otvorte program nanovo!!!!")
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri aktualizácii programu: {e}")
        except FileNotFoundError:
            self.loguj("Príkaz 'curl' alebo 'cp' nebol nájdený.")
        except Exception as e:
            self.loguj(f"Neočakávaná chyba: {e}")

    def loguj(self, sprava):
        cas = QtCore.QTime.currentTime().toString()
        self.log_box.append(f"[{cas}] {sprava}")
        self.log_box.moveCursor(QtGui.QTextCursor.End)

# SplashScreen
class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        pixmap = QtGui.QPixmap("logo.png")
        super().__init__(pixmap)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        self.label = QtWidgets.QLabel(self)
        self.label.setText("Jadiv DEVCONTROL Enterprise\nfor Vihorlat Observatory")
        self.label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setGeometry(0, pixmap.height(), pixmap.width(), 40)

        self.spinner = QtWidgets.QLabel(self)
        movie = QtGui.QMovie("spinner.gif")
        movie.setScaledSize(QtCore.QSize(32, 32))
        self.spinner.setMovie(movie)
        self.spinner.setGeometry((pixmap.width() - 32) // 2, pixmap.height() + 40, 32, 32)
        movie.start()

        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setGeometry(10, pixmap.height() + 80, pixmap.width() - 20, 20)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)

        self.resize(pixmap.width(), pixmap.height() + 110)

    def simulate_loading(self):
        for i in range(101):
            self.progress.setValue(i)
            QtWidgets.qApp.processEvents()
            time.sleep(0.05)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    QtWidgets.qApp.processEvents()

    splash.simulate_loading()

    window = MainWindow()
    window.show()
    splash.finish(window)

    sys.exit(app.exec_())

