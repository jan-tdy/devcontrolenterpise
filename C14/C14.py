import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime

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
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - Version 25-3-2025 02") # Aktualizovaná verzia
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

        # Získanie počiatočného stavu zásuviek
        self.aktualizuj_stav_zasuviek()

        # Spustenie časovača pre pravidelnú aktualizáciu stavu zásuviek (každých 5 minút)
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)
        self.status_timer.start(5 * 60 * 1000) # 5 minút v milisekundách
        
        # Logovacia sekcia
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)
        self.grid_layout.addWidget(self.log_box, 99, 0, 1, 2)


    def aktualizuj_stav_zasuviek(self):
        """Získava a aktualizuje stav všetkých zásuviek."""
        self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aktualizujem stav zásuviek.")
        for name, cislo in ZASUVKY.items():
            self.zisti_stav_zasuvky(cislo, name)

    def zisti_stav_zasuvky(self, cislo_zasuvky, label_name):
        """Zisťuje aktuálny stav danej zásuvky pomocou 'sispmctl -nqg'."""
        try:
            prikaz_stav = f"sispmctl -nqg {cislo_zasuvky}"
            vystup_stav = subprocess.check_output(prikaz_stav, shell=True, text=True).strip()
            if vystup_stav == "1":
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_green.png"))
            elif vystup_stav == "0":
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_red.png"))
            else:
                self.loguj(f"Neočakávaný výstup pre stav zásuvky {cislo_zasuvky}: '{vystup_stav}'")
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri zisťovaní stavu zásuvky {cislo_zasuvky}: {e}")
            self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))
        except FileNotFoundError:
            self.loguj("Príkaz 'sispmctl' nebol nájdený. Nie je možné zistiť stav zásuviek.")
            for name in ZASUVKY:
                self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))

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
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png")) # Predvolená ikona na začiatku
            zapnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut_button, i, 1)
            zasuvky_layout.addWidget(vypnut_button, i, 2)
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png")) # Nastavíme predvolenú ikonu
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
        self.sever_button = QtWidgets.QPushButton("Sever")
        self.juh_button = QtWidgets.QPushButton("Juh")
        self.sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))
        self.juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))

        # Načasovanie strechy
        self.casovac_strechy_group = QtWidgets.QGroupBox("Načasovať strechu")
        casovac_layout = QtWidgets.QGridLayout()
        self.casovac_strechy_enable = QtWidgets.QCheckBox("Aktivovať časovač")
        self.casovac_strechy_enable.stateChanged.connect(self.toggle_casovac_strechy)
        self.casovac_strechy_smer_label = QtWidgets.QLabel("Smer:")
        self.casovac_strechy_smer_combo = QtWidgets.QComboBox()
        self.casovac_strechy_smer_combo.addItem("Sever")
        self.casovac_strechy_smer_combo.addItem("Juh")
        self.casovac_strechy_cas_label = QtWidgets.QLabel("Čas (HH:MM):")
        self.casovac_strechy_cas_input = QtWidgets.QLineEdit()
        self.casovac_strechy_cas_input.setInputMask("HH:MM")
        self.casovac_strechy_button = QtWidgets.QPushButton("Nastaviť časovač")
        self.casovac_strechy_button.clicked.connect(self.nastav_casovac_strechy)
        self.casovac_strechy_button.setEnabled(False) # Na začiatku je časovač vypnutý

        casovac_layout.addWidget(self.casovac_strechy_enable, 0, 0, 1, 2)
        casovac_layout.addWidget(self.casovac_strechy_smer_label, 1, 0)
        casovac_layout.addWidget(self.casovac_strechy_smer_combo, 1, 1)
        casovac_layout.addWidget(self.casovac_strechy_cas_label, 2, 0)
        casovac_layout.addWidget(self.casovac_strechy_cas_input, 2, 1)
        casovac_layout.addWidget(self.casovac_strechy_button, 3, 0, 1, 2)
        self.casovac_strechy_group.setLayout(casovac_layout)

        strecha_layout.addWidget(self.sever_button, 0, 0)
        strecha_layout.addWidget(self.juh_button, 0, 1)
        strecha_group.setLayout(strecha_layout)
        layout.addWidget(strecha_group, 3, 0, 1, 3)
        layout.addWidget(self.casovac_strechy_group, 4, 0, 1, 3)

        group_box.setLayout(layout)
        self.grid_layout.addWidget(group_box, 0, 0)

        # Inicializácia časovača pre načasovanú strechu
        self.strecha_casovac = QtCore.QTimer()
        self.strecha_casovac.timeout.connect(self.skontroluj_cas_strechy)
        self.strecha_casovac.start(60 * 1000) # Kontrola každú minútu
        self.nacasovana_strecha_aktivna = False
        self.nacasovany_smer_strechy = None
        self.nacasovany_cas_strechy = None

    def toggle_casovac_strechy(self, state):
        """Povolí alebo zakáže ovládacie prvky pre časovač strechy."""
        enabled = (state == QtCore.Qt.Checked)
        self.casovac_strechy_smer_combo.setEnabled(enabled)
        self.casovac_strechy_cas_input.setEnabled(enabled)
        self.casovac_strechy_button.setEnabled(enabled)
        if not enabled:
            self.nacasovana_strecha_aktivna = False
            self.nacasovany_smer_strechy = None
            self.nacasovany_cas_strechy = None
            self.loguj("Časovač strechy bol deaktivovaný.")

    def nastav_casovac_strechy(self):
        """Nastaví časovač pre automatické ovládanie strechy."""
        smer = self.casovac_strechy_smer_combo.currentText().lower()
        cas_str = self.casovac_strechy_cas_input.text()

        try:
            datetime.strptime(cas_str, "%H:%M")
            self.nacasovana_strecha_aktivna = True
            self.nacasovany_smer_strechy = smer
            self.nacasovany_cas_strechy = cas_str
            self.loguj(f"Časovač strechy nastavený na {self.nacasovany_cas_strechy} ({self.nacasovany_smer_strechy}).")
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Chyba", "Nesprávny formát času (HH:MM).")

    def skontroluj_cas_strechy(self):
        """Pravidelne kontroluje, či nastal čas pre ovládanie strechy."""
        if self.nacasovana_strecha_aktivna and self.nacasovany_cas_strechy:
            aktualny_cas = datetime.now().strftime("%H:%M")
            if aktualny_cas == self.nacasovany_cas_strechy:
                self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Nastal čas na ovládanie strechy na '{self.nacasovany_smer_strechy}'.")
                self.ovladaj_strechu(self.nacasovany_smer_strechy)
                self.nacasovana_strecha_aktivna = False # Vypneme časovač po vykonaní akcie
                self.casovac_strechy_enable.setChecked(False) # Deaktivujeme aj checkbox
                QtWidgets.QMessageBox.information(self, "Časovač strechy", f"Strecha bola presunutá na '{self.nacasovany_smer_strechy}'. Časovač bol deaktivovaný.")

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
        """Ovláda zadanú zásuvku pomocou príkazu `sispmctl` a následne aktualizuje status."""
        prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        try:
            vystup = subprocess.check_output(prikaz, shell=True)
            self.loguj(vystup.decode())
            # Po úspešnom ovládaní zistíme aktuálny stav a aktualizujeme ikonu
            self.zisti_stav_zasuvky(cislo_zasuvky, label_name)
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
            # Aj po neúspešnom ovládaní sa pokúsime zistiť aktuálny stav (možno sa stav
            self.zisti_stav_zasuvky(cislo_zasuvky, label_name)

    def spusti_indistarter_c14(self):
        """Spustí príkaz `indistarter` na C14."""
        try:
            c14_prikaz = "indistarter"
            c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
            self.loguj(f"INDISTARTER na C14: {c14_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")

    def spusti_indistarter_az2000(self):
        """Spustí príkaz `indistarter` na UVEX-RPi (AZ2000) cez SSH."""
        try:
            uvex_prikaz = f"ssh {SSH_USER2}@{AZ2000_IP} indistarter"
            uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True, text=True, input=f"{SSH_PASS2}\n".encode()) # POZOR: Stále neodporúčané heslo v kóde
            self.loguj(f"INDISTARTER na UVEX-RPi (AZ2000): {uvex_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")
        except FileNotFoundError:
            self.loguj("Príkaz 'ssh' nebol nájdený.")

    def ovladaj_strechu(self, strana):
        """Ovláda strechu (sever/juh) pomocou príkazu `crelay`."""
        if strana == "sever":
            prikaz1 = "crelay -s BITFT 2 ON"
            prikaz2 = "crelay -s BITFT 2 OFF"
        elif strana == "juh":
            prikaz1 = "crelay -s BITFT 1 ON"
            prikaz2 = "crelay -s BITFT 1 OFF"
        else:
            self.loguj("Neplatná strana strechy.")
            return

        try:
            subprocess.run(prikaz1, shell=True, check=True)
            time.sleep(2)
            subprocess.run(prikaz2, shell=True, check=True)
            self.loguj(f"Strecha ({strana}) ovládaná.")
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri ovládaní strechy ({strana}): {e}")
        except FileNotFoundError:
            self.loguj("Príkaz 'crelay' nebol nájdený.")

    def wake_on_lan(self, mac_adresa):
        """Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN."""
        self.loguj(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
        try:
            send_magic_packet(mac_adresa)
        except Exception as e:
            self.loguj(f"Chyba pri odosielaní magic packetu: {e}")

    def aktualizuj_program(self):
        """Aktualizuje program z GitHub repozitára."""
        try:
            # 1. Stiahnutie aktualizovaného súboru
            self.loguj("Aktualizujem program...")
            prikaz_stiahnutie = f"curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/refs/heads/main/C14/C14.py"
            subprocess.run(prikaz_stiahnutie, shell=True, check=True)

            # 2. Nahradenie existujúceho súboru
            prikaz_nahradenie = f"cp C14.py {PROGRAM_CESTA}"
            subprocess.run(prikaz_nahradenie, shell=True, check=True)

            # 3. Reštart aplikácie (ak je to potrebné)
            self.loguj("Program bol aktualizovaný. Zavrite toto okno a otvorte program nanovo!!!!")
            pass
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri aktualizácii programu: {e}")
        except FileNotFoundError:
            self.loguj("Príkaz 'curl' alebo 'cp' nebol nájdený.")
        except Exception as e:
            self.loguj(f"Neočakávaná chyba: {e}")
    def loguj(self, sprava):
        """Zobrazí správu v logovej sekcii."""
        cas = QtCore.QTime.currentTime().toString()
        self.log_box.append(f"[{cas}] {sprava}")
        self.log_box.moveCursor(QtGui.QTextCursor.End)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    hlavne_okno = MainWindow()
    hlavne_okno.show()
    sys.exit(app.exec_())
