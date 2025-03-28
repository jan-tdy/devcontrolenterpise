import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime
import paramiko

# Konštanty pre SSH pripojenie k C14
SSH_USER = "dpv"
SSH_PASS = "otj0711"
C14_IP = "172.20.20.103"  # IP adresa C14

# Konštanty
ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
CENTRAL2_IP = "172.20.20.133" #IP adresa Central2
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"  # Používateľ pre SSH pre iné zariadenia
SSH_PASS2 = "otj0711" # Heslo pre SSH pre iné zariadenia (Pozor: Pre produkčné prostredie použiť SSH kľúče!)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - Version 28-3-2025 02 (SSH)")
        self.setGeometry(100, 100, 800, 600)

        # Inicializácia SSH klienta pre C14
        self.ssh_client_c14 = paramiko.SSHClient()
        self.ssh_client_c14.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Automaticky pridáva neznáme hostiteľské kľúče (neodporúča sa pre produkciu)
        try:
            self.ssh_client_c14.connect(C14_IP, username=SSH_USER, password=SSH_PASS)
            print(f"Úspešne pripojené k C14 na adrese: {C14_IP}")
        except paramiko.AuthenticationException:
            print(f"Chyba autentifikácie pri pripájaní k C14.")
            self.ssh_client_c14 = None
        except paramiko.SSHException as e:
            print(f"Nepodarilo sa vytvoriť SSH spojenie s C14: {e}")
            self.ssh_client_c14 = None
        except Exception as e:
            print(f"Iná chyba pri pripájaní k C14: {e}")
            self.ssh_client_c14 = None

        # Hlavný layout
        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.status_labels = {}
        self.sever_casovac = None
        self.juh_casovac = None
        self.sever_datum_cas_edit = None
        self.juh_datum_cas_edit = None

        # Inicializácia sekcií
        self.init_atacama_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()

    def closeEvent(self, event):
        """Zabezpečí odpojenie SSH klienta pri zatvorení okna."""
        if self.ssh_client_c14:
            self.ssh_client_c14.close()
            print("SSH spojenie s C14 bolo zatvorené.")
        event.accept()

    def _run_remote_command_c14(self, command):
        """Spustí príkaz na C14 cez SSH."""
        if self.ssh_client_c14:
            try:
                stdin, stdout, stderr = self.ssh_client_c14.exec_command(command)
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                if error:
                    print(f"Chyba na C14 pri vykonávaní príkazu '{command}': {error}")
                    return None, error
                else:
                    print(f"Výstup z C14 pre príkaz '{command}': {output}")
                    return output, None
            except paramiko.SSHException as e:
                print(f"SSH chyba pri vykonávaní príkazu '{command}' na C14: {e}")
                return None, str(e)
            except Exception as e:
                print(f"Iná chyba pri vykonávaní príkazu '{command}' na C14: {e}")
                return None, str(e)
        else:
            print("Nie je aktívne SSH spojenie s C14.")
            return None, "Žiadne SSH spojenie"

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
        indistarter_c14_button.clicked(self.spusti_indistarter_c14)
        indistarter_az2000_button.clicked(self.spusti_indistarter_az2000)
        layout.addWidget(indistarter_c14_button, 1, 0, 1, 3)
        layout.addWidget(indistarter_az2000_button, 2, 0, 1, 3) # Pridané tlačidlo pre AZ2000

        # Strecha
        strecha_group = QtWidgets.QGroupBox("Strecha")
        strecha_layout = QtWidgets.QGridLayout()

        # Sever
        sever_label = QtWidgets.QLabel("Sever:")
        sever_button = QtWidgets.QPushButton("Spustiť Sever")
        self.sever_datum_cas_edit = QtWidgets.QLineEdit()
        self.sever_datum_cas_edit.setPlaceholderText("RRRR-MM-DD HH:MM:SS")
        sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))

        strecha_layout.addWidget(sever_label, 0, 0)
        strecha_layout.addWidget(sever_button, 0, 1)
        strecha_layout.addWidget(self.sever_datum_cas_edit, 1, 0, 1, 2)

        # Juh
        juh_label = QtWidgets.QLabel("Juh:")
        juh_button = QtWidgets.QPushButton("Spustiť Juh")
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
        aktualizovat_button.clicked(self.aktualizuj_program)
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
        """Ovláda zadanú zásuvku pomocou príkazu `sispmctl` na C14 cez SSH."""
        prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        vystup, chyba = self._run_remote_command_c14(prikaz)
        if chyba is None:
            if zapnut:
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_green.png"))
            else:
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_red.png"))
        else:
            print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky} na C14: {chyba}")
            self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))

    def spusti_indistarter_c14(self):
        """Spustí príkaz `indistarter` na C14 cez SSH."""
        prikaz = "indistarter"
        vystup, chyba = self._run_remote_command_c14(prikaz)
        if chyba:
            print(f"Chyba pri spúšťaní INDISTARTERA na C14: {chyba}")

    def spusti_indistarter_az2000(self):
        """Spustí príkaz `indistarter` na UVEX-RPi (AZ2000) cez SSH."""
        try:
            uvex_prikaz = f"ssh {SSH_USER2}@{AZ2000_IP} indistarter"
            uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True, input=f"{SSH_PASS2}\n".encode()) # Bezpečnejšie zadávanie hesla (stále neodporúčané pre produkciu)
            print(f"INDISTARTER na UVEX-RPi (AZ2000): {uvex_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            print(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")
        except FileNotFoundError:
            print("Chyba: Príkaz 'ssh' nebol nájdený. Skontrolujte, či je nainštalovaný.")
        except Exception as e:
            print(f"Iná chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")


    def ovladaj_strechu(self, strana):
        """Ovláda strechu (sever/juh) okamžite alebo na zadaný čas."""
        if strana == "sever":
            cas_text = self.sever_datum_cas_edit.text()
        elif strana == "juh":
            cas_text = self.juh_datum_cas_edit.text()
        else:
            print("Neplatná strana strechy.")
            return

        if not cas_text:
            self._spusti_ovladanie_strechy(strana)
        else:
            try:
                planovany_cas = datetime.strptime(cas_text, "%Y-%m-%d %H:%M:%S")
                teraz = datetime.now()
                if planovany_cas <= teraz:
                    self._spusti_ovladanie_strechy(strana)
                else:
                    if strana == "sever":
                        if self.sever_casovac:
                            self.sever_casovac.stop()
                        self.sever_casovac = QtCore.QTimer()
                        self.sever_casovac.timeout.connect(lambda: self._spusti_ovladanie_strechy("sever"))
                        self.sever_casovac.start(int((planovany_cas - teraz).total_seconds()) * 1000)
                        print(f"Spustenie strechy sever naplánované na: {planovany_cas}")
                    elif strana == "juh":
                        if self.juh_casovac:
                            self.juh_casovac.stop()
                        self.juh_casovac = QtCore.QTimer()
                        self.juh_casovac.timeout.connect(lambda: self._spusti_ovladanie_strechy("juh"))
                        self.juh_casovac.start(int((planovany_cas - teraz).total_seconds()) * 1000)
                        print(f"Spustenie strechy juh naplánované na: {planovany_cas}")

            except ValueError:
                print("Neplatný formát času. Použite RRRR-MM-DD HH:MM:SS")

    def _spusti_ovladanie_strechy(self, strana):
        """Spustí príkazy pre ovládanie strechy na C14 cez SSH."""
        if strana == "sever":
            prikaz1 = "crelay -s BITFT 2 ON"
