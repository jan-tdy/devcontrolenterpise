import sys
import subprocess
import time
import random
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime

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

def nahodny_nezmysel():
    nezmysly = [
        "Veveri?ky ovl�dli Wi-Fi a teraz streamuj� orie?ky v 4K.",
        "Teleskop sa rozhodol pozorova? vlastn� skrutky. Revolu?n�!",
        "Server sa zmenil na popkornova?. Pros�m, neprid�vajte maslo.",
        "C14 pr�ve diskutuje o kvantovej filozofii s AZ2000.",
        "Indistarter spustil p�rty. Hudba: transform�torov� ?umy.",
        "Po?asie: 100% pravdepodobnos? padania meteoritov z Excelu.",
        "RC16 po?iadal o dovolenku. D�vod: syndr�m sp�nacieho vy?erpania.",
        "Zapnutie z�suvky vyvolalo z�vanie v Mlie?nej dr�he.",
        "Po zapnut� AZ2000 sa zrodila nov� galaxia. Gratulujeme!",
        "GM3000 za?al p�sa? sonet o volt�?i. Ve?mi siln� nap�tie."
    ]
    return random.choice(nezmysly)

def zobraz_gui_notifikaciu(text):
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(QtWidgets.QMessageBox.Information)
    msg_box.setWindowTitle("?? Hviezdna notifik�cia")
    msg_box.setText(f"<b>{text}</b><br><br><i>{nahodny_nezmysel()}</i>")
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #2b2b2b;
            color: #ffffff;
            font-size: 14px;
            font-family: Consolas, monospace;
            border: 2px solid #00c8ff;
            border-radius: 10px;
            padding: 10px;
        }
        QPushButton {
            background-color: #007acc;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #005f99;
        }
    """)
    msg_box.exec_()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovl�danie Hvezd�rne - C14 - Version 28-3-2025 01")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.status_labels = {}
        self.sever_casovac = None
        self.juh_casovac = None
        self.sever_datum_cas_edit = None
        self.juh_datum_cas_edit = None

        self.init_atacama_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()

    def init_atacama_section(self):
        group_box = QtWidgets.QGroupBox("ATACAMA")
        layout = QtWidgets.QGridLayout()

        zasuvky_layout = QtWidgets.QGridLayout()
        zasuvky_group = QtWidgets.QGroupBox("Z�suvky")
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QtWidgets.QLabel(name)
            zapnut_button = QtWidgets.QPushButton("Zapn�?")
            vypnut_button = QtWidgets.QPushButton("Vypn�?")
            self.status_labels[name] = QtWidgets.QLabel()
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))
            zapnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut_button, i, 1)
            zasuvky_layout.addWidget(vypnut_button, i, 2)
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)
        zasuvky_group.setLayout(zasuvky_layout)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        indistarter_c14_button = QtWidgets.QPushButton("Spusti? INDISTARTER C14")
        indistarter_az2000_button = QtWidgets.QPushButton("Spusti? INDISTARTER AZ2000")
        indistarter_c14_button.clicked.connect(self.spusti_indistarter_c14)
        indistarter_az2000_button.clicked.connect(self.spusti_indistarter_az2000)
        layout.addWidget(indistarter_c14_button, 1, 0, 1, 3)
        layout.addWidget(indistarter_az2000_button, 2, 0, 1, 3)

        strecha_group = QtWidgets.QGroupBox("Strecha")
        strecha_layout = QtWidgets.QGridLayout()

        sever_label = QtWidgets.QLabel("Sever:")
        sever_button = QtWidgets.QPushButton("Spusti? Sever")
        self.sever_datum_cas_edit = QtWidgets.QLineEdit()
        self.sever_datum_cas_edit.setPlaceholderText("RRRR-MM-DD HH:MM:SS")
        sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))

        strecha_layout.addWidget(sever_label, 0, 0)
        strecha_layout.addWidget(sever_button, 0, 1)
        strecha_layout.addWidget(self.sever_datum_cas_edit, 1, 0, 1, 2)

        juh_label = QtWidgets.QLabel("Juh:")
        juh_button = QtWidgets.QPushButton("Spusti? Juh")
        self.juh_datum_cas_edit = QtWidgets.QLineEdit()
        self.juh_datum_cas_edit.setPlaceholderText("RRRR-MM-DD HH:MM:SS")
        juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))

        strecha_layout.addWidget(juh_label, 2, 0)
        strecha_layout.addWidget(juh_button, 2, 1)
        strecha_layout.addWidget(self.juh_datum_cas_edit, 3, 0, 1, 2)

        strecha_group.setLayout(strecha_layout)
        layout.addWidget(strecha_group, 3, 0, 1, 3)

        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 0)

    def init_wake_on_lan_section(self):
        group_box = QtWidgets.QGroupBox("WAKE-ON-LAN")
        layout = QtWidgets.QGridLayout()
        az2000_button = QtWidgets.QPushButton("Zapni AZ2000")
        gm3000_button = QtWidgets.QPushButton("Zapni GM3000")
        az2000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))
        gm3000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))
        layout.addWidget(az2000_button, 0, 0)
        layout.addWidget(gm3000_button, 0, 1)
        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 1)

    def init_ota_section(self):
        group_box = QtWidgets.QGroupBox("OTA Aktualiz�cie")
        layout = QtWidgets.QGridLayout()
        aktualizovat_button = QtWidgets.QPushButton("Aktualizova? program")
        aktualizovat_button.clicked.connect(self.aktualizuj_program)
        layout.addWidget(aktualizovat_button, 0, 0)
        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 1, 0)

        kamera_atacama_label = QtWidgets.QLabel("<a href='http://172.20.20.134'>Kamera Atacama</a>")
        kamera_atacama_label.setOpenExternalLinks(True)
        kamera_astrofoto_label = QtWidgets.QLabel("<a href='http://172.20.20.131'>Kamera Astrofoto</a>")
        kamera_astrofoto_label.setOpenExternalLinks(True)
        self.grid_layout.addWidget(kamera_atacama_label, 1, 1)
        self.grid_layout.addWidget(kamera_astrofoto_label, 2, 1)

