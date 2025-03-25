import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet

# Konštanty
ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
SSH_USER = "dpv"  # Používateľ pre SSH
SSH_PASS = "otj0711" # Heslo pre SSH (Pozor: Pre produkčné prostredie použiť SSH kľúče!)
CENTRAL2_IP = "172.20.20.133" #IP adresa Central2
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"  # Používateľ pre SSH
SSH_PASS2 = "otj0711" # Heslo pre SSH (Pozor: Pre produkčné prostredie použiť SSH kľúče!)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - Version 25-3-2025 01") # Zmenené na C14
        self.setGeometry(100, 100, 800, 600)

        # Hlavný layout
        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.status_labels = {}

        # Inicializácia sekcií
        self.init_atacama_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()

    def init_atacama_section(self):
        """Inicializuje sekciu ATACAMA."""
        group_box = QtWidgets.QGroupBox("ATACAMA")
        layout = QtWidgets.QGridLayout()

        # Zásuvky
        zasuvky_layout = QtWidgets.QGridLayout()
        zasuvky_group = QtWidgets.QGroupBox("Zásuvky")
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QtWidgets.QLabel(name)
            zapnut_button = QtWidgets.QPushButton("Zapnúť")
            vypnut_button = QtWidgets.QPushButton("Vypnúť")
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

        # INDISTARTER
        indistarter_c14_button = QtWidgets.QPushButton("Spustiť INDISTARTER C14")
        indistarter_az2000_button = QtWidgets.QPushButton("Spustiť INDISTARTER AZ2000")
        indistarter_c14_button.clicked.connect(self.spusti_indistarter_c14)
        indistarter_az2000_button.clicked.connect(self.spusti_indistarter_az2000)
        layout.addWidget(indistarter_c14_button, 1, 0, 1, 3)
        layout.addWidget(indistarter_az2000_button, 2, 0, 1, 3) # Pridané tlačidlo pre AZ2000

        # Strecha
        strecha_layout = QtWidgets.QGridLayout()
        strecha_group = QtWidgets.QGroupBox("Strecha")
        sever_button = QtWidgets.QPushButton("Sever")
        juh_button = QtWidgets.QPushButton("Juh")
        sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))
        juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))
        strecha_layout.addWidget(sever_button, 0, 0)
        strecha_layout.addWidget(juh_button, 0, 1)
        strecha_group.setLayout(strecha_layout)
        layout.addWidget(strecha_group, 3, 0, 1, 3) # Zmenené z 2 na 3

        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 0)

    def init_wake_on_lan_section(self):
        """Inicializuje sekciu WAKE-ON-LAN."""
        group_box = QtWidgets.QGroupBox("WAKE-ON-LAN")
        layout = QtWidgets.QGridLayout()
        az2000_button = QtWidgets.QPushButton("Zapni AZ2000")
        gm3000_button = QtWidgets.QPushButton("Zapni GM3000")
        az2000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))  # MAC adresa AZ2000
        gm3000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))  # MAC adresa GM3000
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

    def ovladaj_zasuvku(self, cislo_zasuvky, zapnut, label_name):
        """Ovláda zadanú zásuvku pomocou príkazu `sispmctl`."""
        prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        try:
            vystup = subprocess.check_output(prikaz, shell=True)
            print(vystup.decode())
            if zapnut:
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_green.png"))
            else:
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_red.png"))
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
            self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))

    def spusti_indistarter_c14(self):
        """Spustí príkaz `indistarter` na C14."""
        try:
            c14_prikaz = "indistarter"
            c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
            print(f"INDISTARTER na C14: {c14_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")

    def spusti_indistarter_az2000(self):
        """Spustí príkaz `indistarter` na UVEX-RPi (AZ2000) cez SSH."""
        try:
            uvex_prikaz = f"sshpass -p '{SSH_PASS2}' ssh -o StrictHostKeyChecking=no {SSH_USER2}@{AZ2000_IP} indistarter"
            uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True)
            print(f"INDISTARTER na UVEX-RPi (AZ2000): {uvex_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")


    def ovladaj_strechu(self, strana):
        """Ovláda strechu (sever/juh) pomocou príkazu `crelay`."""
        if strana == "sever":
            prikaz1 = "crelay -s BITFT 2 ON"
            prikaz2 = "crelay -s BITFT 2 OFF"
        elif strana == "juh":
            prikaz1 = "crelay -s BITFT 1 ON"
            prikaz2 = "crelay -s BITFT 1 OFF"
        else:
            print("Neplatná strana strechy.")
            return

        try:
            subprocess.run(prikaz1, shell=True, check=True)
            time.sleep(2)
            subprocess.run(prikaz2, shell=True, check=True)
            print(f"Strecha ({strana}) ovládaná.")
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri ovládaní strechy ({strana}): {e}")

    def wake_on_lan(self, mac_adresa):
        """Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN."""
        # Implementácia Wake-on-LAN (mimo rozsahu tohto príkladu, vyžaduje knižnicu ako wakeonlan)
        print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
        try:
            send_magic_packet(mac_adresa)
        except Exception as e:
            print(f"Chyba pri odosielaní magic packetu: {e}")

    def aktualizuj_program(self):
        """Aktualizuje program z GitHub repozitára."""
        try:
            # 1. Stiahnutie aktualizovaného súboru
            print("Aktualizujem program...")
            prikaz_stiahnutie = f"curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/refs/heads/main/C14/C14.py"
            subprocess.run(prikaz_stiahnutie, shell=True, check=True)

            # 2. Nahradenie existujúceho súboru
            prikaz_nahradenie = f"cp C14.py {PROGRAM_CESTA}"
            subprocess.run(prikaz_nahradenie, shell=True, check=True)

            # 3. Reštart aplikácie (ak je to potrebné)
            print("Program bol aktualizovaný. Zavrite toto okno a otvorte program nanovo!!!!")
            pass
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri aktualizácii programu: {e}")
        except Exception as e:
            print(f"Neočakávaná chyba: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    hlavne_okno = MainWindow()
    hlavne_okno.show()
    sys.exit(app.exec_())
