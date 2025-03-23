import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QGridLayout, QWidget, QGroupBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# Konštanty
PROGRAM_GITHUB = "github.com/jan-tdy/devcontrolenterpise-ordervtdy01dpv-main/main.py"
PROGRAM_CESTA = "/home/dpv/devcontrolenterpise/central2.py"  # Cesta k súboru central2.py
SSH_USER = "dpv"
SSH_PASS = "otj0711"
C14_IP = "172.20.20.103"  # IP adresa C14

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - Central2")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.init_atacama_section()
        self.init_astrofoto_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()
        self.status_labels = {}

    def init_atacama_section(self):
        """Inicializuje sekciu ATACAMA."""
        group_box = QGroupBox("ATACAMA")
        layout = QGridLayout()

        # Zásuvky
        zasuvky_layout = QGridLayout()
        zasuvky_group = QGroupBox("Zásuvky")
        zasuvky_names = ["NOUT", "C14", "RC16"]
        for i, name in enumerate(zasuvky_names):
            label = QLabel(name)
            zapnut_button = QPushButton("Zapnúť")
            vypnut_button = QPushButton("Vypnúť")
            self.status_labels[name] = QLabel()
            self.status_labels[name].setText('<i class="fas fa-circle text-red-500"></i>')
            zapnut_button.clicked.connect(lambda _, n=name: self.ovladaj_zasuvku_atacama(n, True))
            vypnut_button.clicked.connect(lambda _, n=name: self.ovladaj_zasuvku_atacama(n, False))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut_button, i, 1)
            zasuvky_layout.addWidget(vypnut_button, i, 2)
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)
        zasuvky_group.setLayout(zasuvky_layout)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        # INDISTARTER
        indistarter_button = QPushButton("Spustiť INDISTARTER na C14 a UVEX-RPI")
        indistarter_button.clicked.connect(self.spusti_indistarter_atacama)
        layout.addWidget(indistarter_button, 1, 0, 1, 3)

        # Strecha
        strecha_layout = QGridLayout()
        strecha_group = QGroupBox("Strecha")
        sever_button = QPushButton("Sever")
        juh_button = QPushButton("Juh")
        sever_button.clicked.connect(lambda: self.ovladaj_strechu_atacama("sever"))
        juh_button.clicked.connect(lambda: self.ovladaj_strechu_atacama("juh"))
        strecha_layout.addWidget(sever_button, 0, 0)
        strecha_layout.addWidget(juh_button, 0, 1)
        strecha_group.setLayout(strecha_layout)
        layout.addWidget(strecha_group, 2, 0, 1, 3)

        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 0)

    def init_astrofoto_section(self):
        """Inicializuje sekciu ASTROFOTO."""
        group_box = QGroupBox("ASTROFOTO")
        layout = QGridLayout()

        zasuvky_layout = QGridLayout()
        zasuvky_group = QGroupBox("Zásuvky")
        zasuvky_names = ["PARMEZAN", "ONTC", "KK MALY"]
        for i, name in enumerate(zasuvky_names):
            label = QLabel(name)
            zapnut_button = QPushButton("Zapnúť")
            vypnut_button = QPushButton("Vypnúť")
            self.status_labels[name] = QLabel()
            self.status_labels[name].setText('<i class="fas fa-circle text-red-500"></i>')
            zapnut_button.clicked.connect(lambda _, n=name: self.ovladaj_zasuvku_astrofoto(n, True))
            vypnut_button.clicked.connect(lambda _, n=name: self.ovladaj_zasuvku_astrofoto(n, False))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut_button, i, 1)
            zasuvky_layout.addWidget(vypnut_button, i, 2)
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)
        zasuvky_group.setLayout(zasuvky_layout)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        indistarter_button = QPushButton("Spustiť INDISTARTER na ONTC, KK 30CM a KK MALY")
        indistarter_button.clicked.connect(self.spusti_indistarter_astrofoto)
        layout.addWidget(indistarter_button, 1, 0, 1, 3)

        strecha_layout = QGridLayout()
        strecha_group = QGroupBox("Strecha")
        west_button = QPushButton("Západ")
        east_button = QPushButton("Východ")
        west_button.clicked.connect(lambda: self.ovladaj_strechu_astrofoto("west"))
        east_button.clicked.connect(lambda: self.ovladaj_strechu_astrofoto("east"))
        strecha_layout.addWidget(west_button, 0, 0)
        strecha_layout.addWidget(east_button, 0, 1)
        strecha_group.setLayout(strecha_layout)
        layout.addWidget(strecha_group, 2, 0, 1, 3)

        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 1)

    def init_wake_on_lan_section(self):
        """Inicializuje sekciu WAKE-ON-LAN."""
        group_box = QGroupBox("WAKE-ON-LAN")
        layout = QGridLayout()
        az2000_button = QPushButton("Zapni AZ2000")
        gm3000_button = QPushButton("Zapni GM3000")
        az2000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))
        gm3000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))
        layout.addWidget(az2000_button, 0, 0)
        layout.addWidget(gm3000_button, 0, 1)
        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 1, 0)

    def init_ota_section(self):
        """Inicializuje sekciu OTA Aktualizácie."""
        group_box = QGroupBox("OTA Aktualizácie")
        layout = QGridLayout()
        aktualizovat_button = QPushButton("Aktualizovať program")
        aktualizovat_button.clicked.connect(self.aktualizuj_program)
        layout.addWidget(aktualizovat_button, 0, 0)
        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 1, 1)

        kamera_atacama_label = QLabel(
            "<a href='http://172.20.20.134'>Kamera Atacama</a>")
        kamera_atacama_label.setOpenExternalLinks(True)
        kamera_astrofoto_label = QLabel(
            "<a href='http://172.20.20.131'>Kamera Astrofoto</a>")
        kamera_astrofoto_label.setOpenExternalLinks(True)
        self.grid_layout.addWidget(kamera_atacama_label, 2, 0)
        self.grid_layout.addWidget(kamera_astrofoto_label, 2, 1)

    def ovladaj_zasuvku_atacama(self, zasuvka, zapnut):
        """Ovláda zásuvky v ATACAMA (cez C14)."""
        if zasuvka == "NOUT":
            cislo_zasuvky = 4
        elif zasuvka == "C14":
            cislo_zasuvky = 3
        elif zasuvka == "RC16":
            cislo_zasuvky = 2
        else:
            print(f"Neplatná zásuvka: {zasuvka}")
            return

        prikaz = f"ssh {SSH_USER}@{C14_IP} sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        try:
            vystup = subprocess.check_output(prikaz, shell=True, timeout=10)
            print(vystup.decode())
            if zapnut:
                self.status_labels[zasuvka].setText('<i class="fas fa-circle text-green-500"></i>')
            else:
                self.status_labels[zasuvka].setText('<i class="fas fa-circle text-red-500"></i>')
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri ovládaní zásuvky {zasuvka} v ATACAMA: {e}")
            self.status_labels[zasuvka].setText('<i class="fas fa-circle text-red-500"></i>')
        except TimeoutError:
            print(f"Chyba: Časový limit prekročený pri ovládaní zásuvky {zasuvka} v ATACAMA")
            self.status_labels[zasuvka].setText('<i class="fas fa-circle text-red-500"></i>')

    def ovladaj_zasuvku_astrofoto(self, zasuvka, zapnut):
        """Ovláda zásuvky v ASTROFOTO."""
        #  Implementácia ovládania zásuviek pre ASTROFOTO (ak je iný systém)
        print(f"Ovládanie zásuvky {zasuvka} v ASTROFOTO (zapnut={zapnut})")
        if zapnut:
            self.status_labels[zasuvka].setText('<i class="fas fa-circle text-green-500"></i>')
        else:
            self.status_labels[zasuvka].setText('<i class="fas fa-circle text-red-500"></i>')

    def spusti_indistarter_atacama(self):
        """Spustí INDISTARTER na C14 a UVEX-RPi (cez SSH)."""
        try:
            c14_prikaz = f"ssh {SSH_USER}@{C14_IP} indistarter"
            c14_vystup = subprocess.check_output(c14_prikaz, shell=True, timeout=10)
            print(f"INDISTARTER na C14: {c14_vystup.decode()}")

            uvex_prikaz = f"ssh {SSH_USER}@{CENTRAL2_IP} indistarter"
            uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True, timeout=10)
            print(f"INDISTARTER na UVEX-RPi: {uvex_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri spúšťaní INDISTARTERA v ATACAMA: {e}")
        except TimeoutError:
            print(f"Chyba: Časový limit prekročený pri spúšťaní INDISTARTERA v ATACAMA")

    def spusti_indistarter_astrofoto(self):
        """Spustí INDISTARTER na zariadení v ASTROFOTO."""
        #  Implementácia spustenia INDISTARTERA pre ASTROFOTO
        print("Spúšťam INDISTARTER pre ASTROFOTO")

    def ovladaj_strechu_atacama(self, strana):
        """Ovláda strechu v ATACAMA (cez C14)."""
        if strana == "sever":
            prikaz1 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 2 ON"
            prikaz2 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 2 OFF"
        elif strana == "juh":
            prikaz1 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 1 ON"
            prikaz2 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 1 OFF"
        else:
            print("Neplatná strana strechy.")
            return
        try:
            subprocess.run(prikaz1, shell=True, check=True, timeout=10)
            time.sleep(2)
            subprocess.run(prikaz2, shell=True, check=True, timeout=10)
            print(f"Strecha ATACAMA ({strana}) ovládaná.")
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri ovládaní strechy ATACAMA ({strana}): {e}")
        except TimeoutError:
            print(f"Chyba: Časový limit prekročený pri ovládaní strechy ATACAMA ({strana})")

    def ovladaj_strechu_astrofoto(self, strana):
        """Ovláda strechu v ASTROFOTO."""
        #  Implementácia ovládania strechy pre ASTROFOTO
        print(f"Ovládanie strechy ASTROFOTO ({strana})")

    def wake_on_lan(self, mac_adresa):
        """Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN."""
        print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
        try:
            # from wakeonlan import send_magic_packet
            # send_magic_packet(mac_adresa)
            pass  # Odstrániť pass a odkomentovať riadky vyššie
        except Exception as e:
            print(f"Chyba pri odosielaní magic packetu: {e}")

    def aktualizuj_program(self):
        """Aktualizuje program z GitHub repozitára."""
        try:
            print("Aktualizujem program...")
            prikaz_stiahnutie = f"curl -O https://{PROGRAM_GITHUB}"
            subprocess.run(prikaz_stiahnutie, shell=True, check=True)
            prikaz_nahradenie = f"cp main.py {PROGRAM_CESTA}"
            subprocess.run(prikaz_nahradenie, shell=True, check=True)
            print("Program bol aktualizovaný. Reštartujem aplikáciu...")
            # Otázka: Ako reštartovať aplikáciu?
            # sem pride kod na restart
            pass
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri aktualizácii programu: {e}")
        except Exception as e:
            print(f"Neočakávaná chyba: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hlavne_okno = MainWindow()
    hlavne_okno.show()
    sys.exit(app.exec_())
