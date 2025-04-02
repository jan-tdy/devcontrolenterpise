import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime
import pytz

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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - Version 25-3-2025 02")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.setLayout(self.grid_layout)

        self.status_labels = {}

        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)
        self.grid_layout.addWidget(self.log_box, 99, 0, 1, 2)

        self.init_atacama_section()
        self.init_wake_on_lan_section()
        self.init_ota_section()

        self.aktualizuj_stav_zasuviek()
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)
        self.status_timer.start(5 * 60 * 1000)

    def aktualizuj_stav_zasuviek(self):
        self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aktualizujem stav zásuviek.")
        for name, cislo in ZASUVKY.items():
            self.zisti_stav_zasuvky(cislo, name)

    def zisti_stav_zasuvky(self, cislo_zasuvky, label_name):
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
        group_box = QtWidgets.QGroupBox("ATACAMA")
        layout = QtWidgets.QGridLayout()

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
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)
        zasuvky_group.setLayout(zasuvky_layout)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        indistarter_c14_button = QtWidgets.QPushButton("Spustiť INDISTARTER C14")
        indistarter_az2000_button = QtWidgets.QPushButton("Spustiť INDISTARTER AZ2000")
        indistarter_c14_button.clicked.connect(self.spusti_indistarter_c14)
        indistarter_az2000_button.clicked.connect(self.spusti_indistarter_az2000)
        layout.addWidget(indistarter_c14_button, 1, 0, 1, 3)
        layout.addWidget(indistarter_az2000_button, 2, 0, 1, 3)

        strecha_layout = QtWidgets.QGridLayout()
        strecha_group = QtWidgets.QGroupBox("Strecha")
        self.sever_button = QtWidgets.QPushButton("Sever")
        self.juh_button = QtWidgets.QPushButton("Juh")
        self.sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))
        self.juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))

        self.casovac_strechy_group = QtWidgets.QGroupBox("Načasovať strechu")
        casovac_layout = QtWidgets.QGridLayout()
        self.casovac_strechy_enable = QtWidgets.QCheckBox("Aktivovať časovač")
        self.casovac_strechy_enable.stateChanged.connect(self.toggle_casovac_strechy)
        self.casovac_strechy_smer_label = QtWidgets.QLabel("Smer (sever/juh):")
        self.casovac_strechy_smer_combo = QtWidgets.QComboBox()
        self.casovac_strechy_smer_combo.addItem("sever")
        self.casovac_strechy_smer_combo.addItem("juh")
        self.casovac_strechy_cas_label = QtWidgets.QLabel("Čas (YYYY-MM-DD HH:MM):")
        self.casovac_strechy_cas_input = QtWidgets.QLineEdit()
        self.casovac_strechy_cas_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self.casovac_strechy_button = QtWidgets.QPushButton("Nastaviť časovač")
        self.casovac_strechy_button.clicked.connect(self.nastav_casovac_strechy)
        self.casovac_strechy_button.setEnabled(False)

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

        self.strecha_casovac = QtCore.QTimer()
        self.strecha_casovac.timeout.connect(self.skontroluj_cas_strechy)
        self.strecha_casovac.start(60 * 1000)
        self.nacasovana_strecha_aktivna = False
        self.nacasovany_smer_strechy = None
        self.nacasovany_cas_strechy_utc = None

    def toggle_casovac_strechy(self, state):
        enabled = (state == QtCore.Qt.Checked)
        self.casovac_strechy_smer_combo.setEnabled(enabled)
        self.casovac_strechy_cas_input.setEnabled(enabled)
        self.casovac_strechy_button.setEnabled(enabled)
        if not enabled:
            self.nacasovana_strecha_aktivna = False
            self.nacasovany_smer_strechy = None
            self.nacasovany_cas_strechy_utc = None
            self.loguj("Časovač strechy bol deaktivovaný.")

    def nastav_casovac_strechy(self):
        smer = self.casovac_strechy_smer_combo.currentText().lower()
        teraz = datetime.now(pytz.utc)
        cas_utc_str = teraz.strftime("%Y-%m-%d %H:%M")
        self.casovac_strechy_cas_input.setText(cas_utc_str)
        self.nacasovana_strecha_aktivna = True
        self.nacasovany_smer_strechy = smer
        self.nacasovany_cas_strechy_utc = cas_utc_str
        self.loguj(f"Časovač strechy nastavený na {self.nacasovany_cas_strechy_utc} UTC ({self.nacasovany_smer_strechy}).")

    def skontroluj_cas_strechy(self):
        if self.nacasovana_strecha_aktivna and self.nacasovany_cas_strechy_utc:
            try:
                nacasovany_cas_dt = pytz.utc.localize(datetime.strptime(self.nacasovany_cas_strechy_utc, "%Y-%m-%d %H:%M"))
                teraz_utc = datetime.now(pytz.utc)
                if teraz_utc >= nacasovany_cas_dt:
                    self.loguj(
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Nastal čas (UTC) na ovládanie strechy na '{self.nacasovany_smer_strechy}'.")
                    self.ovladaj_strechu(self.nacasovany_smer_strechy)
                    self.nacasovana_strecha_aktivna = False
                    self.casovac_strechy_enable.setChecked(False)
                    QtWidgets.QMessageBox.information(self, "Časovač strechy",
                                                      f"Strecha bola presunutá na '{self.nacasovany_smer_strechy}' o {self.nacasovany_cas_strechy_utc} UTC. Časovač bol deaktivovaný.")
            except ValueError:
                self.loguj(f"Chyba pri kontrole času strechy: Nesprávny formát času: {self.nacasovany_cas_strechy_utc}")
                self.nacasovana_strecha_aktivna = False
                self.casovac_strechy_enable.setChecked(False)

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
        group_box = QtWidgets.QGroupBox("OTA Aktualizácie")
        layout = QtWidgets.QGridLayout()
        aktualizovat_button = QtWidgets.QPushButton("Aktualizovať program")
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

    def ovladaj_zasuvku(self, cislo_zasuvky, zapnut, label_name):
        prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
        try:
            vystup = subprocess.check_output(prikaz, shell=True)
            self.loguj(vystup.decode())
            self.zisti_stav_zasuvky(cislo_zasuvky, label_name)
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
            self.zisti_stav_zasuvky(cislo_zasuvky, label_name)

    def spusti_indistarter_c14(self):
        try:
            c14_prikaz = "indistarter"
            c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
            self.loguj(f"INDISTARTER na C14: {c14_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")

    def spusti_indistarter_az2000(self):
        try:
            uvex_prikaz = f"ssh {SSH_USER2}@{AZ2000_IP} indistarter"
            uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True, text=True,
                                                  input=f"{SSH_PASS2}\n".encode())
            self.loguj(f"INDISTARTER na UVEX-RPi (AZ2000): {uvex_vystup.decode()}")
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")
        except FileNotFoundError:
            self.loguj("Príkaz 'ssh' nebol nájdený.")

    def ovladaj_strechu(self, strana):
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
        self.loguj(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
        try:
            send_magic_packet(mac_adresa)
        except Exception as e:
            self.loguj(f"Chyba pri odosielaní magic packetu: {e}")

    def aktualizuj_program(self):
        try:
            self.loguj("Aktualizujem program...")
            prikaz_stiahnutie = f"curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/refs/heads/main/C14/C14.py"
            subprocess.run(prikaz_stiahnutie, shell=True, check=True)

            prikaz_nahradenie = f"cp C14.py {PROGRAM_CESTA}"
            subprocess.run(prikaz_nahradenie, shell=True, check=True)

            self.loguj("Program bol aktualizovaný. Zavrite toto okno a otvorte program nanovo!!!!")
            pass
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri aktualizácii programu: {e}")
        except FileNotFoundError:
            self.loguj("Príkaz 'curl' alebo 'cp' nebol nájdený.")
        except Exception as e:
            self.loguj(f"Neočakávaná chyba: {e}")

    def loguj(self, sprava):
        cas = QtCore.QTime.currentTime().toString()
        self.log_box.append(f"[{cas}] {sprava}")
        self.log_box.moveCursor(QtGui.QTextCursor.End)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    hlavne_okno = MainWindow()
    hlavne_okno.show()
    sys.exit(app.exec_())
