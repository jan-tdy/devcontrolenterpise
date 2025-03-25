import sys
import subprocess
import time
import socket
import webbrowser
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QPushButton,
                             QLineEdit, QMessageBox, QFrame, QSizePolicy, QScrollArea)
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

        # Nastavenie globálneho štýlu aplikácie
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF; /* Biele pozadie */
                color: #2c3e50;
            }
            QWidget {
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                color: #2c3e50;
            }
            QLabel {
                color: #2c3e50;
            }
            QPushButton {
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                cursor: pointer;
                transition: background-color 0.3s ease, color 0.3s ease;
            }
            QPushButton:hover {
                background-color: #bdc3c7; /* Svetlejšie šedé pri najetí */
                color: #2c3e50;
            }
            QPushButton:pressed {
                background-color: #95a5a6; /* Ešte svetlejšie šedé pri stlačení */
                color: #2c3e50;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                padding: 8px;
                margin: 5px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                box-shadow: 0 0 5px rgba(52, 152, 219, 0.5);
                outline: none;
            }
            QFrame {
                border: 1px solid #7f8c8d;
                border-radius: 10px;
                margin: 10px;
                padding: 10px;
                background-color: #ecf0f1;
            }
            QScrollArea {
                background-color: #ecf0f1;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #ecf0f1;
                width: 10px;
                margin: 20px 0 20px 0;
            }
            QScrollBar::handle:vertical {
                background: #7f8c8d;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 20px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 20px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

        """)

        grid_layout = QGridLayout()
        self.main_layout.addLayout(grid_layout)

        # ATACAMA sekcia
        atacama_frame = QFrame()
        atacama_layout = QVBoxLayout()

        atacama_label = QLabel("ATACAMA")
        atacama_label.setFont(QFont("Arial", 14, QFont.Bold))
        atacama_label.setAlignment(Qt.AlignCenter)
        atacama_layout.addWidget(atacama_label)

        zasuvky_frame = QFrame()
        zasuvky_layout = QGridLayout()
        zasuvky_label = QLabel("Zásuvky")
        zasuvky_label.setFont(QFont("Arial", 12, QFont.Bold))
        zasuvky_layout.addWidget(zasuvky_label, 0, 0, 1, len(ZASUVKY))

        self.led_labels = {}
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            zapnut_button = QPushButton("Zapnúť")
            zapnut_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50; /* Green */
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 14px;
                    margin: 4px 8px;
                    cursor: pointer;
                    transition-duration: 0.4s;
                }

                QPushButton:hover {
                    background-color: #45a049;
                }

                QPushButton:active {
                  background-color: #367c39;
                }
                """)
            vypnut_button = QPushButton("Vypnúť")
            vypnut_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336; /* Red */
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 14px;
                    margin: 4px 8px;
                    cursor: pointer;
                    transition-duration: 0.4s;
                }

                QPushButton:hover {
                    background-color: #d32f2f;
                }

                QPushButton:active {
                  background-color: #c62828;
                }
                """)

            led_label = QLabel()
            led_label.setPixmap(QPixmap(LED_DEF_PATH))
            led_label.setFixedSize(20, 20)
            self.led_labels[cislo] = led_label

            zapnut_button.clicked.connect(lambda: ovladaj_zasuvku(cislo, True, self.led_labels[cislo]))
            vypnut_button.clicked.connect(lambda: ovladaj_zasuvku(cislo, False, self.led_labels[cislo]))

            zasuvky_layout.addWidget(label, i + 1, 0)
            zasuvky_layout.addWidget(zapnut_button, i + 1, 1)
            zasuvky_layout.addWidget(vypnut_button, i + 1, 2)
            zasuvky_layout.addWidget(led_label, i+1, 3)
        zasuvky_frame.setLayout(zasuvky_layout)
        atacama_layout.addWidget(zasuvky_frame)

        indistarter_c14_button = QPushButton("Spustiť INDISTARTER C14")
        indistarter_c14_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA; /* Blue */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 8px;
                cursor: pointer;
                transition-duration: 0.4s;
              }

              QPushButton:hover {
                background-color: #007ba7;
              }

              QPushButton:active {
                background-color: #00668e;
              }
            """);
        indistarter_az2000_button = QPushButton("Spustiť INDISTARTER AZ2000")
        indistarter_az2000_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA; /* Blue */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 8px;
                cursor: pointer;
                transition-duration: 0.4s;
              }

              QPushButton:hover {
                background-color: #007ba7;
              }

              QPushButton:active {
                background-color: #00668e;
              }
            """);
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
        sever_button.setStyleSheet("""
            QPushButton {
                background-color: #FF851B; /* Orange */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 8px;
                cursor: pointer;
                transition-duration: 0.4s;
              }

              QPushButton:hover {
                background-color: #d86e00;
              }

              QPushButton:active {
                background-color: #b85e00;
              }
            """);
        juh_button = QPushButton("Juh")
        juh_button.setStyleSheet("""
            QPushButton {
                background-color: #FF851B; /* Orange */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 8px;
                cursor: pointer;
                transition-duration: 0.4s;
              }

              QPushButton:hover {
                background-color: #d86e00;
              }

              QPushButton:active {
                background-color: #b85e00;
              }
            """);
        sever_button.clicked.connect(lambda: ovladaj_strechu("sever"))
        juh_button.clicked.connect(lambda: ovladaj_strechu("juh"))
        strecha_layout.addWidget(sever_button)
        strecha_layout.addWidget(juh_button)
        strecha_frame.setLayout(strecha_layout)
        atacama_layout.addWidget(strecha_frame)

        atacama_frame.setLayout(atacama_layout)
        grid_layout.addWidget(atacama_frame, 0, 0)

        # WAKE-ON-LAN sekcia
        wake_frame = QFrame()
        wake_layout = QVBoxLayout()
        wake_label = QLabel("WAKE-ON-LAN")
        wake_label.setFont(QFont("Arial", 14, QFont.Bold))
        wake_label.setAlignment(Qt.AlignCenter)
        wake_layout.addWidget(wake_label)
        az2000_button = QPushButton("Zapni AZ2000")
        az2000_button.setStyleSheet("background-color: #e0e0e0; color: #2c3e50;");
        gm3000_button = QPushButton("Zapni GM3000")
        gm3000_button.setStyleSheet("background-color: #e0e0e0; color: #2c3e50;");
        az2000_button.clicked.connect(lambda: wake_on_lan("00:c0:08:a9:c2:32"))
        gm3000_button.clicked.connect(lambda: wake_on_lan(GM3000_MAC))
        wake_layout.addWidget(az2000_button)
        wake_layout.addWidget(gm3000_button)
        wake_frame.setLayout(wake_layout)
        grid_layout.addWidget(wake_frame, 0, 1)

        # OTA Aktualizácie sekcia
        ota_frame = QFrame()
        ota_layout = QVBoxLayout()
        ota_label = QLabel("OTA Aktualizácie")
        ota_label.setFont(QFont("Arial", 14, QFont.Bold))
        ota_label.setAlignment(Qt.AlignCenter)
        ota_layout.addWidget(ota_label)
        aktualizovat_button = QPushButton("Aktualizovať program")
        aktualizovat_button.setStyleSheet("background-color: #e0e0e0; color: #2c3e50;");
        aktualizovat_button.clicked.connect(aktualizuj_program)
        ota_layout.addWidget(aktualizovat_button)

        kamera_atacama_label = QLabel('<a href="http://172.20.20.134">Kamera Atacama</a>')
        kamera_atacama_label.setOpenExternalLinks(True)
        kamera_atacama_label.setCursor(Qt.PointingHandCursor)
        kamera_atacama_label.setAlignment(Qt.AlignCenter)
        ota_layout.addWidget(kamera_atacama_label)

        kamera_astrofoto_label = QLabel('<a href="http://172.20.20.131">Kamera Astrofoto</a>')
        kamera_astrofoto_label.setOpenExternalLinks(True)
        kamera_astrofoto_label.setCursor(Qt.PointingHandCursor)
        kamera_astrofoto_label.setAlignment(Qt.AlignCenter)
        ota_layout.addWidget(kamera_astrofoto_label)

        ota_frame.setLayout(ota_layout)
        grid_layout.addWidget(ota_frame, 0, 2)

        # Konfig sekcia
        config_frame = QFrame()
        config_layout = QGridLayout()
        config_label = QLabel("Konfigurácia AZ2000")
        config_label.setFont(QFont("Arial", 14, QFont.Bold))
        config_label.setAlignment(Qt.AlignCenter)
        config_layout.addWidget(config_label, 0, 0, 1, 3)

        ip_label = QLabel("IP adresa:")
        ip_label.setAlignment(Qt.AlignLeft)
        self.ip_input = QLineEdit(AZ2000_IP)
        user_label = QLabel("SSH používateľ:")
        user_label.setAlignment(Qt.AlignLeft)
        self.user_input = QLineEdit(SSH_USER2)
        password_label = QLabel("SSH heslo:")
        password_label.setAlignment(Qt.AlignLeft)
        self.password_input = QLineEdit(SSH_PASS2)
        self.password_input.setEchoMode(QLineEdit.Password)
        save_button = QPushButton("Uložiť nastavenia")
        save_button.setStyleSheet("background-color: #e0e0e0; color: #2c3e50;");
        save_button.clicked.connect(self.on_save_config)

        config_layout.addWidget(ip_label, 1, 0)
        config_layout.addWidget(self.ip_input, 2, 0)
        config_layout.addWidget(user_label, 1, 1)
        config_layout.addWidget(self.user_input, 2, 1)
        config_layout.addWidget(password_label, 1, 2)
        config_layout.addWidget(self.password_input, 2, 2)
        config_layout.addWidget(save_button, 1, 3, 2, 1)
        config_frame.setLayout(config_layout)
        grid_layout.addWidget(config_frame, 0, 3)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        grid_layout.setColumnStretch(3, 1)

    def on_save_config(self):
        """
        Uloží konfiguráciu AZ2000 (IP adresa, používateľské meno, heslo) do konfiguračného súboru.
        Zobrazí informačné alebo chybové okno v závislosti od výsledku uloženia.
        Aktualizuje globálne premenné s novými hodnotami.
        """
        global AZ2000_IP, SSH_USER2, SSH_PASS2
        ip = self.ip_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        if save_config(ip, user, password):
            AZ2000_IP = ip
            SSH_USER2 = user
            SSH_PASS2 = password
            QMessageBox.information(self, "Úspech", "Konfigurácia AZ2000 bola úspešne uložená.")
        else:
            QMessageBox.critical(self, "Chyba", "Chyba pri ukladaní konfigurácie AZ2000.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
