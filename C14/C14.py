# Licensed under the JADIV Private License v1.0 – see LICENSE file for details.
import sys
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

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
        pix = QtGui.QPixmap("logo.png")
        super().__init__(pix)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        # License text
        lic = QtWidgets.QLabel(
            "Licensed under the JADIV Private License v1.0 – see LICENSE file for details.",
            self
        )
        lic.setStyleSheet("color: blue; font-size: 8px;")
        lic.setAlignment(QtCore.Qt.AlignCenter)
        lic.setGeometry(0, pix.height(), pix.width(), 20)

        # Title text
        lbl = QtWidgets.QLabel(
            "Jadiv DEVCONTROL Enterprise for Vihorlat Observatory",
            self
        )
        lbl.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setGeometry(0, pix.height() + 20, pix.width(), 40)

        # Progress bar
        self.pr = QtWidgets.QProgressBar(self)
        self.pr.setGeometry(10, pix.height() + 70, pix.width() - 20, 20)
        self.pr.setRange(0, 100)
        self.pr.setValue(0)
        self.pr.setTextVisible(False)

        # QTimer for fake loading
        self._counter = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)  # ~4 seconds total

        self.resize(pix.width(), pix.height() + 100)

    def _tick(self):
        self._counter += 1
        self.pr.setValue(self._counter)
        if self._counter >= 100:
            self._timer.stop()
            self._finish()

    def _finish(self):
        # Lazy imports for main functionality
        import subprocess
        from wakeonlan import send_magic_packet
        from datetime import datetime
        import pytz

        # Show main window
        self.main = MainWindow(subprocess, send_magic_packet, datetime, pytz)
        self.main.show()
        self.finish(self.main)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, subprocess, send_magic_packet, datetime, pytz):
        super().__init__()
        self.subprocess = subprocess
        self.send_magic_packet = send_magic_packet
        self.datetime = datetime
        self.pytz = pytz

        self.setWindowTitle("Ovládanie Hvezdárne - C14 - Version 25-3-2025 02")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout(self.main_layout)

        self.status_labels = {}
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)
        self.grid_layout.addWidget(self.log_box, 99, 0, 1, 3)

        self.init_atacama_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()

        self.aktualizuj_stav_zasuviek()
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)
        self.status_timer.start(5 * 60 * 1000)

    def init_atacama_section(self):
        group_box = QtWidgets.QGroupBox("ATACAMA")
        layout = QtWidgets.QGridLayout(group_box)

        # Zásuvky
        zasuvky_group = QtWidgets.QGroupBox("Zásuvky")
        zasuvky_layout = QtWidgets.QGridLayout(zasuvky_group)
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QtWidgets.QLabel(name)
            zapnut = QtWidgets.QPushButton("Zapnúť")
            vypnut = QtWidgets.QPushButton("Vypnúť")
            self.status_labels[name] = QtWidgets.QLabel()
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))
            zapnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut, i, 1)
            zasuvky_layout.addWidget(vypnut, i, 2)
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        # INDISTARTER
        ind_c14 = QtWidgets.QPushButton("Spustiť INDISTARTER C14")
        ind_az = QtWidgets.QPushButton("Spustiť INDISTARTER AZ2000")
        ind_c14.clicked.connect(self.spusti_indistarter_c14)
        ind_az.clicked.connect(self.spusti_indistarter_az2000)
        layout.addWidget(ind_c14, 1, 0, 1, 3)
        layout.addWidget(ind_az, 2, 0, 1, 3)

        # Strecha
        strecha_group = QtWidgets.QGroupBox("Strecha")
        strecha_layout = QtWidgets.QGridLayout(strecha_group)
        self.sever_button = QtWidgets.QPushButton("Sever")
        self.juh_button = QtWidgets.QPushButton("Juh")
        self.both_button = QtWidgets.QPushButton("Both")
        self.sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))
        self.juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))
        self.both_button.clicked.connect(lambda: self.ovladaj_strechu("both"))
        strecha_layout.addWidget(self.sever_button, 0, 0)
        strecha_layout.addWidget(self.juh_button, 0, 1)
        strecha_layout.addWidget(self.both_button, 0, 2)
        layout.addWidget(strecha_group, 3, 0, 1, 3)

        # Časovač strechy
        cas_group = QtWidgets.QGroupBox("Načasovať strechu")
        cas_layout = QtWidgets.QGridLayout(cas_group)
        self.cas_enable = QtWidgets.QCheckBox("Aktivovať časovač")
        self.cas_enable.stateChanged.connect(self.toggle_casovac_strechy)
        self.cas_smer = QtWidgets.QComboBox()
        self.cas_smer.addItems(["sever", "juh", "both"])
        self.cas_input = QtWidgets.QLineEdit()
        self.cas_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self.cas_btn = QtWidgets.QPushButton("Nastaviť časovač")
        self.cas_btn.clicked.connect(self.nastav_casovac_strechy)
        self.cas_btn.setEnabled(False)
        cas_layout.addWidget(self.cas_enable, 0, 0, 1, 2)
        cas_layout.addWidget(QtWidgets.QLabel("Smer:"), 1, 0)
        cas_layout.addWidget(self.cas_smer, 1, 1)
        cas_layout.addWidget(QtWidgets.QLabel("Čas:"), 2, 0)
        cas_layout.addWidget(self.cas_input, 2, 1)
        cas_layout.addWidget(self.cas_btn, 3, 0, 1, 2)
        layout.addWidget(cas_group, 4, 0, 1, 3)

        self.grid_layout.addWidget(group_box, 0, 0)

        # Timer strechy
        self.timer_strecha = QtCore.QTimer()
        self.timer_strecha.timeout.connect(self.skontroluj_cas_strechy)
        self.timer_strecha.start(60 * 1000)
        self.c_act = False
        self.c_smer = None
        self.c_time = None

    def init_wake_on_lan_section(self):
        group_box = QtWidgets.QGroupBox("WAKE-ON-LAN")
        layout = QtWidgets.QGridLayout(group_box)
        az2000 = QtWidgets.QPushButton("Zapni AZ2000")
        gm3000 = QtWidgets.QPushButton("Zapni GM3000")
        az2000.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))
        gm3000.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))
        layout.addWidget(az2000, 0, 0)
        layout.addWidget(gm3000, 0, 1)
        self.grid_layout.addWidget(group_box, 0, 1)

    def init_ota_section(self):
        group_box = QtWidgets.QGroupBox("OTA Aktualizácie")
        layout = QtWidgets.QGridLayout(group_box)
        aktualizovat = QtWidgets.QPushButton("Aktualizovať program")
        aktualizovat.clicked.connect(self.aktualizuj_program)
        layout.addWidget(aktualizovat, 0, 0)
        self.grid_layout.addWidget(group_box, 1, 0)
        kamera_atacama = QtWidgets.QLabel("<a href='http://172.20.20.134'>Kamera Atacam
