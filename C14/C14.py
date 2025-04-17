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

class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        pixmap = QtGui.QPixmap("logo.png")
        super().__init__(pixmap)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        self.label = QtWidgets.QLabel(self)
        self.label.setText("Jadiv DEVCONTROL Enterprise\nfor Vihorlat Observatory")
        self.label.setStyleSheet("color: blue; font-size: 160px; font-weight: bold;")
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
            time.sleep(0.04)

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
