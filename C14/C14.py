import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

# Konštanty
ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2
}
PROGRAM_GITHUB = "github.com/jan-tdy/devcontrolenterpise-ordervtdy01dpv-atacama/main.py"
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/main.py"
SSH_USER = "dpv"  # Používateľ pre SSH
SSH_PASS = "otj0711" # Heslo pre SSH (Pozor: Pre produkčné prostredie použiť SSH kľúče!)
CENTRAL2_IP = "172.20.20.133" #IP adresa Central2

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14")
        self.setGeometry(100, 100, 800, 600)  # Nastavenie veľkosti okna

        # Hlavný layout
        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

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
            self.status_labels[name] = QtWidgets.QLabel()  # Pridaj statusny label
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_red.png"))  # Predvolene nastav červenú
            zapnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut_button, i, 1)
            zasuvky_layout.addWidget(vypnut_button, i, 2)
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)  # Pridaj statusny label do layoutu
        zasuvky_group.setLayout(zasuvky_layout)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        # INDISTARTER
        indistarter_button = QtWidgets.QPushButton("Spustiť INDISTARTER")
        indistarter_button.clicked.connect(self.spusti_indistarter)
        layout.addWidget(indistarter_button, 1, 0, 1, 3)

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
        layout.addWidget(strecha_group, 2, 0, 1, 3)

        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 0)
        self.status_labels = {}

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
        kamera_atacama_label.setOpenExternalLinks(True)  # Aby sa otvoril link v prehliadači
        kamera_astrofoto_label = QtWidgets.QLabel("<a href='http://172.20.20.131'>Kamera Astrofoto</a>")
        kamera_astrofoto_label.setOpenExternalLinks(True)
        self.grid_layout.addWidget(kamera_atacama_label, 1, 1)
        self.grid_layout.addWidget(kamera_astrofoto_label, 2, 1)

    def ovladaj_zasuvku(self, cislo_zasuvky, zapnut, label_name):
        """Ovláda zadanú zásuvku pomocou príkazu `sispmctl`."""
        prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        try:
            vystup = subprocess.check_output(prikaz, shell=True)  # Spustí príkaz a získa výstup
            print(vystup.decode())  # Vypíše výstup príkazu
            if zapnut:
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_green.png"))
            else:
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_red.png"))

        except subprocess.CalledProcessError as e:
            print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
            self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_red.png"))

    def spusti_indistarter(self):
        """Spustí príkaz `indistarter` na C14 a UVEX-RPi (cez SSH)."""
        try:
            # Spustenie na C14
            c14_prikaz = "indistarter"
            c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
            print(f"INDISTARTER na C14: {c14_vystup.decode()}")

            # Spustenie na UVEX-RPi (cez SSH)
            uvex_prikaz = f"ssh {SSH_USER}@{AZ2000_IP} {c14_prikaz}"
            uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True, password=SSH_PASS) #POZOR: Heslo by nemalo byt v kode
            print(f"INDISTARTER na UVEX-RPi: {uvex_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri spúšťaní INDISTARTERA: {e}")

    def ovladaj_strechu(self, strana):
        """Ovláda strechu (sever/juh) pomocou príkazu `crelay`."""
        if strana == "sever":
            prikaz1 = "crelay -s BI TFT 2 ON"
            prikaz2 = "crelay -s BI TFT 2 OFF"
        elif strana == "juh":
            prikaz1 = "crelay -s BI TFT 1 ON"
            prikaz2 = "crelay -s BI TFT 1 OFF"
        else:
            print("Neplatná strana strechy.")
            return

        try:
            subprocess.run(prikaz1, shell=True, check=True)  # Použi run pre jednoduchšie spustenie
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
            #Príklad:
            #from wakeonlan import send_magic_packet
            #send_magic_packet(mac_adresa)
            pass #odstranit pass a odkomentovat riadky vyssie
        except Exception as e:
            print(f"Chyba pri odosielaní magic packetu: {e}")

    def aktualizuj_program(self):
        """Aktualizuje program z GitHub repozitára."""
        try:
            # 1. Stiahnutie aktualizovaného súboru
            print("Aktualizujem program...")
            # Otázka: Ako presne stiahnuť súbor z GitHub repozitára?  Použiť napr. `git clone` alebo `curl`?
            # Predpokladám, že `curl`:
            prikaz_stiahnutie = f"curl -O https://{PROGRAM_GITHUB}"  # -O zachová pôvodný názov súboru
            subprocess.run(prikaz_stiahnutie, shell=True, check=True)

            # 2. Nahradenie existujúceho súboru
            prikaz_nahradenie = f"cp main.py {PROGRAM_CESTA}"  # Predpoklad, že stiahnutý súbor je v aktuálnom adresári
            subprocess.run(prikaz_nahradenie, shell=True, check=True)

            # 3. Reštart aplikácie (ak je to potrebné)
            print("Program bol aktualizovaný. Reštartujem aplikáciu...")
            # Otázka: Ako reštartovať aplikáciu? Závisí od spôsobu spustenia.  Napr. `sys.executable` pre reštart aktuálneho skriptu.
            #sys.executable
            # sem pride kod na restart
            pass #odstranit pass a odkomentovat riadok vyssie
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri aktualizácii programu: {e}")
        except Exception as e:
            print(f"Neočakávaná chyba: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    hlavne_okno = MainWindow()
    hlavne_okno.show()
    sys.exit(app.exec_())
