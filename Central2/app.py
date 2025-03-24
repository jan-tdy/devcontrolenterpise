import sys
import subprocess
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

# Konštanty
PROGRAM_GITHUB = "github.com/jan-tdy/devcontrolenterpise-ordervtdy01dpv-main/main.py"
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/main.py"
SSH_USER = "dpv"
SSH_PASS = "otj0711" #POZOR: Heslo by nemalo byt v kode
C14_IP = "172.20.20.103"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - Central2")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.status_labels = {}  # Inicializácia self.status_labels

        self.init_c14_control_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()
        
        

    def init_c14_control_section(self):
        """Inicializuje sekciu pre ovládanie C14."""
        group_box = QtWidgets.QGroupBox("Ovládanie C14")
        layout = QtWidgets.QGridLayout()

        # Zásuvky na C14
        c14_zasuvky_layout = QtWidgets.QGridLayout()
        c14_zasuvky_group = QtWidgets.QGroupBox("Zásuvky C14")
        zasuvky = {"NOUT": 4, "C14": 3, "RC16": 2}
        for i, (name, cislo) in enumerate(zasuvky.items()):
            label = QtWidgets.QLabel(name)
            zapnut_button = QtWidgets.QPushButton("Zapnúť")
            vypnut_button = QtWidgets.QPushButton("Vypnúť")
            self.status_labels[name] = QtWidgets.QLabel()
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_red.png"))
            zapnut_button.clicked.connect(lambda _, n=cislo: self.ovladaj_zasuvku_c14(n, True, name))
            vypnut_button.clicked.connect(lambda _, n=cislo: self.ovladaj_zasuvku_c14(n, False, name))
            c14_zasuvky_layout.addWidget(label, i, 0)
            c14_zasuvky_layout.addWidget(zapnut_button, i, 1)
            c14_zasuvky_layout.addWidget(vypnut_button, i, 2)
            c14_zasuvky_layout.addWidget(self.status_labels[name], i, 3)
        c14_zasuvky_group.setLayout(c14_zasuvky_layout)
        layout.addWidget(c14_zasuvky_group, 0, 0, 1, 3)

        # INDISTARTER na C14 a UVEX-RPi
        indistarter_button = QtWidgets.QPushButton("Spustiť INDISTARTER na C14/UVEX")
        indistarter_button.clicked.connect(self.spusti_indistarter_c14)
        layout.addWidget(indistarter_button, 1, 0, 1, 3)

        # Strecha na C14
        strecha_layout = QtWidgets.QGridLayout()
        strecha_group = QtWidgets.QGroupBox("Strecha C14")
        sever_button = QtWidgets.QPushButton("Sever")
        juh_button = QtWidgets.QPushButton("Juh")
        sever_button.clicked.connect(lambda: self.ovladaj_strechu_c14("sever"))
        juh_button.clicked.connect(lambda: self.ovladaj_strechu_c14("juh"))
        strecha_layout.addWidget(sever_button, 0, 0)
        strecha_layout.addWidget(juh_button, 0, 1)
        strecha_group.setLayout(strecha_layout)
        layout.addWidget(strecha_group, 2, 0, 1, 3)

        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 0)

    def init_wake_on_lan_section(self):
        """Inicializuje sekciu WAKE-ON-LAN."""
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
        """Inicializuje sekciu OTA Aktualizácie."""
        group_box = QtWidgets.QGroupBox("OTA Aktualizácie")
        layout = QtWidgets.QGridLayout()
        aktualizovat_button = QtWidgets.QPushButton("Aktualizovať program")
        aktualizovat_button.clicked.connect(self.aktualizuj_program)
        layout.addWidget(aktualizovat_button, 0, 0)
        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 1, 0)
        
        # Pridanie linkov na kamery
        kamera_atacama_label = QtWidgets.QLabel("<a href='http://172.20.20.134'>Kamera Atacama</a>")
        kamera_atacama_label.setOpenExternalLinks(True)
        kamera_astrofoto_label = QtWidgets.QLabel("<a href='http://172.20.20.131'>Kamera Astrofoto</a>")
        kamera_astrofoto_label.setOpenExternalLinks(True)
        self.grid_layout.addWidget(kamera_atacama_label, 1, 1)
        self.grid_layout.addWidget(kamera_astrofoto_label, 2, 1)

    def ovladaj_zasuvku_c14(self, cislo_zasuvky, zapnut, label_name):
        """Ovláda zásuvku na C14 cez SSH."""
        prikaz = f"ssh {SSH_USER}@{C14_IP} sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        try:
            vystup = subprocess.check_output(prikaz, shell=True, password=SSH_PASS) #POZOR: Heslo by nemalo byt v kode
            print(vystup.decode())
            if zapnut:
                self.status_lab
