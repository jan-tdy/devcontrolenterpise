import sys
import subprocess
import time
import socket
import webbrowser
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QPushButton,
                             QLineEdit, QMessageBox, QFrame, QSizePolicy, QScrollArea,
                             QSpacerItem, QTabWidget)
from PyQt5.QtGui import QFont, QCursor, QPixmap, QColor
from PyQt5.QtCore import Qt, QTimer

# Konštanty
ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2,
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
CONFIG_FILE = "az2000_config.txt"
LED_GREEN_PATH = "/home/dpv/j44softapps-socketcontrol/led_green.png"
LED_RED_PATH = "/home/dpv/j44softapps-socketcontrol/led_red.png"
LED_DEF_PATH = "/home/dpv/j44softapps-socketcontrol/led_def.png"

# Premenné pre konfiguráciu AZ2000
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"
SSH_PASS2 = "otj0711"
GM3000_MAC = "00:c0:08:aa:35:12"

# Funkcie
def load_config():
    """
    Načíta konfiguráciu AZ2000 z konfiguračného súboru.
    Ak súbor neexistuje, použije predvolené hodnoty a vytvorí prázdny konfiguračný súbor.
    V prípade inej chyby pri čítaní súboru vypíše chybovú správu.
    """
    global AZ2000_IP, SSH_USER2, SSH_PASS2
    try:
        with open(CONFIG_FILE, "r") as f:
            lines = f.readlines()
            if len(lines) >= 3:
                AZ2000_IP = lines[0].strip()
                SSH_USER2 = lines[1].strip()
                SSH_PASS2 = lines[2].strip()
    except FileNotFoundError:
        print("Konfiguračný súbor nebol nájdený. Používajú sa predvolené hodnoty.")
        try:
            with open(CONFIG_FILE, "w") as f:
                pass
        except Exception as e:
            print(f"Chyba pri vytváraní prázdneho konfiguračného súboru: {e}")
    except Exception as e:
        print(f"Chyba pri načítaní konfigurácie: {e}")

def save_config(ip, user, password):
    """
    Uloží konfiguráciu AZ2000 (IP adresa, používateľské meno, heslo) do konfiguračného súboru.
    V prípade úspešného uloženia vráti True, inak vráti False a vypíše chybovú správu.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(f"{ip}\n")
            f.write(f"{user}\n")
            f.write(f"{password}\n")
        print("Konfigurácia AZ2000 bola uložená.")
        return True
    except Exception as e:
        print(f"Chyba pri ukladaní konfigurácie: {e}")
        return False

def ovladaj_zasuvku(cislo_zasuvky, zapnut, label_widget):
    """
    Ovláda zadanú zásuvku (zapnutie alebo vypnutie) pomocou externého príkazu `sispmctl`.
    Aktualizuje farbu LEDky v GUI na zeleno pri zapnutí, červeno pri vypnutí a šedo pri chybe.

    Parametre:
    cislo_zasuvky (int): Číslo zásuvky, ktorá sa má ovládať.
    zapnut (bool): True pre zapnutie, False pre vypnutie.
    label_widget (QLabel): Objekt Labelu z GUI, ktorý reprezentuje LEDku pre danú zásuvku.
    """
    prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
    try:
        vystup = subprocess.check_output(prikaz, shell=True)
        print(vystup.decode())
        if zapnut:
            label_widget.setPixmap(QPixmap(LED_GREEN_PATH))
        else:
            label_widget.setPixmap(QPixmap(LED_RED_PATH))
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
        label_widget.setPixmap(QPixmap(LED_DEF_PATH))

def spusti_indistarter_c14():
    """
    Spustí príkaz `indistarter` na lokálnom počítači (C14).
    Tento príkaz pravdepodobne spúšťa nejakú inú aplikáciu alebo službu.
    """
    try:
        c14_prikaz = "indistarter"
        c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
        print(f"INDISTARTER na C14: {c14_vystup.decode()}")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")

def spusti_indistarter_az2000():
    """
    Spustí príkaz `indistarter` na vzdialenom počítači (AZ2000) cez SSH pripojenie.
    Používa `sshpass` pre zadanie hesla neinteraktívne (POZOR: Bezpečné len v obmedzených prípadoch!).
    """
    global AZ2000_IP, SSH_USER2, SSH_PASS2
    try:
        uvex_prikaz = f"sshpass -p '{SSH_PASS2}' ssh -o StrictHostKeyChecking=no {SSH_USER2}@{AZ2000_IP} 'indistarter'"
        subprocess.run(uvex_prikaz, shell=True, check=True)
        print(f"INDISTARTER na UVEX-RPi (AZ2000) spustený.")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")

def ovladaj_strechu(strana):
    """
    Ovláda strechu (sever alebo juh) pomocou externého príkazu `crelay`.
    Spustí dva príkazy pre otvorenie a zatvorenie strechy pre zadanú stranu.
    """
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

def wake_on_lan(mac_adresa):
    """
    Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN.
    Nahrádza volanie externého skriptu priamym kódom v Pythone.

    Parameter:
    mac_adresa (str): MAC adresa zariadenia, ktoré sa má prebudiť (napr. "00:11:22:33:44:55").
    """
    print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
    try:
        mac_bytes = bytes.fromhex(mac_adresa.replace(':', ''))
        packet = b'\xff' * 6 + mac_bytes * 16
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(packet, ('<broadcast>', 9))
        print("Magic packet odoslaný.")
    except Exception as e:
        print(f"Chyba pri odosielaní magic packetu: {e}")
        QMessageBox.critical(None, "Chyba", f"Chyba pri odosielaní WOL paketu: {e}")

def aktualizuj_program():
    """
    Aktualizuje program z GitHub repozitára.
    Implementované priamo v Pythone namiesto volania externého skriptu.
    Zastaví bežiaci program, stiahne novú verziu a reštartuje aplikáciu.
    """
    try:
        print("Aktualizujem program...")
        prikaz_zastavenie = "pkill -f 'python3 /home/dpv/j44softapps-socketcontrol/C14.py'"
        subprocess.run(prikaz_zastavenie, shell=True, check=False)

        os.chdir("/home/dpv/j44softapps-socketcontrol/")

        url = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py"
        prikaz_stiahnutie = f"curl -O {url}"
        subprocess.run(prikaz_stiahnutie, shell=True, check=True)

        print("Stiahnutá nová verzia programu.")

        prikaz_restart = "python3 /home/dpv/j44softapps-socketcontrol/C14.py &"
        subprocess.Popen(prikaz_restart, shell=True, close_fds=True)
        print("Program reštartovaný na pozadí.")
        QApplication.quit()
    except Exception as e:
        print(f"Chyba pri aktualizácii: {e}")
        QMessageBox.critical(None, "Chyba", f"Chyba pri aktualizácii: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14")
        self.setGeometry(100, 100, 800, 600)
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        load_config()

        # Používame QTabWidget pre hlavné rozdelenie okna
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Vytvoríme widget pre každú záložku
        self.atacama_tab = QWidget()
        self.wake_tab = QWidget()
        self.konfig_tab = QWidget()

        # Pridáme záložky do QTabWidget
        self.tabs.addTab(self.atacama_tab, "ATACAMA")
        self.tabs.addTab(self.wake_tab, "WAKE-ON-LAN")
        self.tabs.addTab(self.konfig_tab, "Konfigurácia")

        # Rozloženie pre ATACAMA záložku
        atacama_layout = QVBoxLayout()
        self.atacama_tab.setLayout(atacama_layout)

        # ATACAMA sekcia
        atacama_label = QLabel("ATACAMA")
        atacama_label.setFont(QFont("Arial", 14, QFont.Bold))
        atacama_label.setAlignment(Qt.AlignCenter)
        atacama_layout.addWidget(atacama_label)

        zasuvky_frame = QFrame()
        zasuvky_layout = QGridLayout()
        zasuvky_label = QLabel("Zásuvky")
        zasuvky_label.setFont(QFont("Arial", 12, QFont.Bold))
        zasuvky_layout.addWidget(zasuvky_label, 0, 0, 1, 4)

        self.led_labels = {}
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            zapnut_button = QPushButton("Zapnúť")
            vypnut_button = QPushButton("Vypnúť")
            led_label = QLabel()
            led_label.setPixmap(QPixmap(LED_DEF_PATH))
            led_label.setFixedSize(20, 20)
            self.led_labels[cislo] = led_label

            zapnut_button.clicked.connect(lambda: ovladaj_zasuvku(cislo, True, self.led_labels[cislo]))
            vypnut_button.clicked.connect(lambda: ovladaj_zasuvku(cislo, False, self.led_labels[cislo]))

            zasuvky_layout.addWidget(label, i + 1, 0)
            zasuvky_layout.addWidget(zapnut_button, i + 1, 1)
            zasuvky_layout.addWidget(vypnut_button, i + 1, 2)
            zasuvky_layout.addWidget(led_label, i + 1, 3)

        zasuvky_frame.setLayout(zasuvky_layout)
        atacama_layout.addWidget(zasuvky_frame)

        indistarter_c14_button = QPushButton("Spustiť INDISTARTER C14")
        indistarter_az2000_button = QPushButton("Spustiť INDISTARTER AZ2000")
        indistarter_c14_button.clicked.connect(spusti_indistarter_c14)
        indistarter_az2000_button.clicked.connect(spusti_indistarter_az2000)
        atacama_layout.addWidget(indistarter_c14_button)
        atacama_layout.addWidget(indistarter_az2000_button)

        strecha_frame = QFrame()
        strecha_layout = QHBoxLayout()
        strecha_label = QLabel("Strecha")
        strecha_label.setFont(QFont("Arial", 12, QFont.Bold))
        strecha_layout.addWidget(strecha_label)
        strecha_layout.setAlignment(Qt.AlignCenter)
        sever_button = QPushButton("Sever")
        juh_button = QPushButton("Juh")
        sever_button.clicked.connect(lambda: ovladaj_strechu("sever"))
        juh_button.clicked.connect(lambda: ovladaj_strechu("juh"))
        strecha_layout.addWidget(sever_button)
        strecha_layout.addWidget(juh_button)
        strecha_frame.setLayout(strecha_layout)
        atacama_layout.addWidget(strecha_frame)

        # Rozloženie pre WAKE-ON-LAN záložku
        wake_layout = QVBoxLayout()
        self.wake_tab.setLayout(wake_layout)

        # WAKE-ON-LAN sekcia
        wake_label = QLabel("WAKE-ON-LAN")
        wake_label.setFont(QFont("Arial", 14, QFont.Bold))
        wake_label.setAlignment(Qt.AlignCenter)
        wake_layout.addWidget(wake_label)
        az2000_button = QPushButton("Zapni AZ2000")
        gm3000_button = QPushButton("Zapni GM3000")
        az2000_button.clicked.connect(lambda: wake_on_lan("00:c0:08:a9:c2:32"))
        gm3000_button.clicked.connect(lambda: wake_on_lan(GM3000_MAC))
        wake_layout.addWidget(az2000_button)
        wake_layout.addWidget(gm3000_button)

        # Rozloženie pre Konfig záložku
        konfig_layout = QVBoxLayout()
        self.konfig_tab.setLayout(konfig_layout)

        # OTA Aktualizácie sekcia
        ota_frame = QFrame()
        ota_layout = QVBoxLayout()
        ota_label = QLabel("OTA Aktualizácie")
        ota_label.setFont(QFont("Arial", 14, QFont.Bold))
        ota_label.setAlignment(Qt.AlignCenter)
        ota_layout.addWidget(ota_label)
        aktualizovat_button = QPushButton("Aktualizovať program")
        aktualizovat_button.clicked.connect(aktualizuj_program)
        ota_layout.addWidget(aktualizovat_button)

        kamera_atacama_label = QLabel('<a href="http://172.20.20.121">Kamera ATACAMA</a>')
        kamera_atacama_label.setOpenExternalLinks(True)
        ota_layout.addWidget(kamera_atacama_label)

        konfig_layout.addWidget(ota_frame)

        # Konfig sekcia
        konfig_frame = QFrame()
        konfig_layout_grid = QGridLayout()
        konfig_label = QLabel("Konfigurácia")
        konfig_label.setFont(QFont("Arial", 14, QFont.Bold))
        konfig_label.setAlignment(Qt.AlignCenter)
        konfig_layout_grid.addWidget(konfig_label, 0, 0, 1, 2)

        ip_label = QLabel("IP AZ2000:")
        self.ip_edit = QLineEdit(AZ2000_IP)
        user_label = QLabel("SSH User:")
        self.user_edit = QLineEdit(SSH_USER2)
        password_label = QLabel("SSH Pass:")
        self.password_edit = QLineEdit(SSH_PASS2)
        ulozit_button = QPushButton("Uložiť")
        ulozit_button.clicked.connect(self.ulozit_konfiguraciu)

        konfig_layout_grid.addWidget(ip_label, 1, 0)
        konfig_layout_grid.addWidget(self.ip_edit, 1, 1)
        konfig_layout_grid.addWidget(user_label, 2, 0)
        konfig_layout_grid.addWidget(self.user_edit, 2, 1)
        konfig_layout_grid.addWidget(password_label, 3, 0)
        konfig_layout_grid.addWidget(self.password_edit, 3, 1)
        konfig_layout_grid.addWidget(ulozit_button, 4, 0, 1, 2)

        konfig_frame.setLayout(konfig_layout_grid)
        konfig_layout.addWidget(konfig_frame)

        self.setLayout(self.main_layout)

    def ulozit_konfiguraciu(self):
        """Uloží konfiguráciu zadanú v textových poliach."""
        ip = self.ip_edit.text()
        user = self.user_edit.text()
        password = self.password_edit.text()
        if save_config(ip, user, password):
            QMessageBox.information(self, "Úspech", "Konfigurácia bola úspešne uložená.")
            load_config()  # Načíta novú konfiguráciu
        else:
            QMessageBox.critical(self, "Chyba", "Chyba pri ukladaní konfigurácie.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hlavne_okno = MainWindow()
    hlavne_okno.show()
    sys.exit(app.exec_())
