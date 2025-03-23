import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QGridLayout, QWidget, QGroupBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import socket
import threading

# Konštanty
ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2
}
PROGRAM_GITHUB = "github.com/jan-tdy/devcontrolenterpise-ordervtdy01dpv-atacama/main.py"
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/main.py"
SSH_USER = "dpv"  # Používateľ pre SSH
SSH_PASS = "otj0711"  # Heslo pre SSH (Pozor: Pre produkčné prostredie použiť SSH kľúče!)
CENTRAL2_IP = "172.20.20.133"  # IP adresa Central2
SSH_PORT = 2222  # Port pre SSH server (zmeňte, ak je port 22 obsadený)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14")
        self.setGeometry(100, 100, 800, 600)  # Nastavenie veľkosti okna

        # Hlavný layout
        self.main_layout = QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.status_labels = {}  # Inicializácia self.status_labels
        # Inicializácia sekcií
        self.init_atacama_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()

        # Spustenie SSH servera v samostatnom vlákne
        self.ssh_thread = threading.Thread(target=self.start_ssh_server)
        self.ssh_thread.daemon = True  # Nastavíme vlákno ako démon, aby sa ukončilo s hlavným vláknom
        self.ssh_thread.start()

    def init_atacama_section(self):
        """Inicializuje sekciu ATACAMA."""
        group_box = QGroupBox("ATACAMA")
        layout = QGridLayout()

        # Zásuvky
        zasuvky_layout = QGridLayout()
        zasuvky_group = QGroupBox("Zásuvky")
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QLabel(name)
            zapnut_button = QPushButton("Zapnúť")
            vypnut_button = QPushButton("Vypnúť")
            self.status_labels[name] = QLabel()  # Pridaj statusny label
            self.status_labels[name].setText(
                '<i class="fas fa-circle text-red-500"></i>')  # Predvolene nastav červenú ikonu
            zapnut_button.clicked.connect(
                lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut_button.clicked.connect(
                lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut_button, i, 1)
            zasuvky_layout.addWidget(vypnut_button, i, 2)
            zasuvky_layout.addWidget(
                self.status_labels[name], i, 3)  # Pridaj statusny label do layoutu
        zasuvky_group.setLayout(zasuvky_layout)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        # INDISTARTER
        indistarter_button = QPushButton("Spustiť INDISTARTER")
        indistarter_button.clicked.connect(self.spusti_indistarter)
        layout.addWidget(indistarter_button, 1, 0, 1, 3)

        # Strecha
        strecha_layout = QGridLayout()
        strecha_group = QGroupBox("Strecha")
        sever_button = QPushButton("Sever")
        juh_button = QPushButton("Juh")
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
        group_box = QGroupBox("WAKE-ON-LAN")
        layout = QGridLayout()
        az2000_button = QPushButton("Zapni AZ2000")
        gm3000_button = QPushButton("Zapni GM3000")
        az2000_button.clicked.connect(
            lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))  # MAC adresa AZ2000
        gm3000_button.clicked.connect(
            lambda: self.wake_on_lan("00:c0:08:aa:35:12"))  # MAC adresa GM3000
        layout.addWidget(az2000_button, 0, 0)
        layout.addWidget(gm3000_button, 0, 1)
        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 1)

    def init_ota_section(self):
        """Inicializuje sekciu OTA Aktualizácie."""
        group_box = QGroupBox("OTA Aktualizácie")
        layout = QGridLayout()
        aktualizovat_button = QPushButton("Aktualizovať program")
        aktualizovat_button.clicked.connect(self.aktualizuj_program)
        layout.addWidget(aktualizovat_button, 0, 0)
        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 1, 0)

        # Pridanie linkov na kamery
        kamera_atacama_label = QLabel(
            "<a href='http://172.20.20.134'>Kamera Atacama</a>")
        kamera_atacama_label.setOpenExternalLinks(
            True)  # Aby sa otvoril link v prehliadači
        kamera_astrofoto_label = QLabel(
            "<a href='http://172.20.20.131'>Kamera Astrofoto</a>")
        kamera_astrofoto_label.setOpenExternalLinks(True)
        self.grid_layout.addWidget(kamera_atacama_label, 1, 1)
        self.grid_layout.addWidget(kamera_astrofoto_label, 2, 1)

    def ovladaj_zasuvku(self, cislo_zasuvky, zapnut, label_name):
        """Ovláda zadanú zásuvku pomocou príkazu `sispmctl`."""
        prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        try:
            vystup = subprocess.check_output(
                prikaz, shell=True)  # Spustí príkaz a získa výstup
            print(vystup.decode())  # Vypíše výstup príkazu
            if zapnut:
                self.status_labels[
                    label_name].setText('<i class="fas fa-circle text-green-500"></i>')  # Nastav zelenú ikonu
            else:
                self.status_labels[
                    label_name].setText('<i class="fas fa-circle text-red-500"></i>')  # Nastav červenú ikonu

        except subprocess.CalledProcessError as e:
            print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
            self.status_labels[label_name].setText(
                '<i class="fas fa-circle text-red-500"></i>')

    def spusti_indistarter(self):
        """Spustí príkaz `indistarter` na C14 a UVEX-RPi (cez SSH)."""
        try:
            # Spustenie na C14
            c14_prikaz = "indistarter"
            c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
            print(f"INDISTARTER na C14: {c14_vystup.decode()}")

            # Spustenie na UVEX-RPi (cez SSH)
            uvex_prikaz = f"ssh {SSH_USER}@{CENTRAL2_IP} {c14_prikaz}"
            uvex_vystup = subprocess.check_output(
                uvex_prikaz, shell=True, password=SSH_PASS)  # POZOR: Heslo by nemalo byt v kode
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
            subprocess.run(prikaz1, shell=True,
                             check=True)  # Použi run pre jednoduchšie spustenie
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
            # Príklad:
            # from wakeonlan import send_magic_packet
            # send_magic_packet(mac_adresa)
            pass  # odstranit pass a odkomentovat riadky vyssie
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
            # sys.executable
            # sem pride kod na restart
            pass  # odstranit pass a odkomentovat riadok vyssie
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri aktualizácii programu: {e}")
        except Exception as e:
            print(f"Neočakávaná chyba: {e}")

    def start_ssh_server(self):
        """Spustí jednoduchý socket server, ktorý počúva príkazy."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', SSH_PORT))  # Počúvame na všetkých rozhraniach
        sock.listen(1)  # Maximálne 1 pripojenie v rade

        print(f"SSH server spustený na porte {SSH_PORT}...")

        while True:
            conn, addr = sock.accept()
            print(f"Pripojenie od: {addr}")
            try:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    prikaz = data.decode().strip()
                    print(f"Prijatý príkaz: {prikaz}")
                    self.spracuj_prikaz(prikaz)
                    conn.sendall("OK\n".encode())  # Potvrdenie prijatia príkazu
            except Exception as e:
                print(f"Chyba pri komunikácii s klientom: {e}")
            finally:
                conn.close()
                print("Pripojenie ukončené.")

    def spracuj_prikaz(self, prikaz):
        """Spracuje prijatý príkaz."""
        if prikaz.startswith("zasuvka"):
            casti = prikaz.split()
            if len(casti) == 4:
                zasuvka = casti[1]
                stav = casti[2]
                label_name = casti[3]
                if zasuvka in ZASUVKY and stav in ("on", "off"):
                    cislo_zasuvky = ZASUVKY[zasuvka]
                    zapnut = stav == "on"
                    self.ovladaj_zasuvku(cislo_zasuvky, zapnut, label_name)
                else:
                    print(f"Neplatný príkaz: {prikaz}")
            else:
                print(f"Neplatný príkaz: {prikaz}")
        elif prikaz == "indistarter":
            self.spusti_indistarter()
        elif prikaz.startswith("strecha"):
            casti = prikaz.split()
            if len(casti) == 2:
                strana = casti[1]
                self.ovladaj_strechu(strana)
            else:
                print(f"Neplatný príkaz: {prikaz}")
        elif prikaz.startswith("wakeonlan"):
            casti = prikaz.split()
            if len(casti) == 2:
                mac_adresa = casti[1]
                self.wake_on_lan(mac_adresa)
            else:
                print(f"Neplatný príkaz: {prikaz}")
        else:
            print(f"Neznámy príkaz: {prikaz}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    hlavne_okno = MainWindow()
    hlavne_okno.show()
    sys.exit(app.exec_())
