import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime
import pytz  # Import knižnice pre prácu s časovými zónami

# Konštanty - definície premenných, ktoré sa v programe nemenia
ZASUVKY = {
    "NOUT": 4,  # Číslo zásuvky pre "NOUT"
    "C14": 3,  # Číslo zásuvky pre "C14"
    "RC16": 2   # Číslo zásuvky pre "RC16"
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"  # Cesta k spustiteľnému súboru programu
SSH_USER = "dpv"  # Používateľské meno pre SSH pripojenie
SSH_PASS = "otj0711"  # Heslo pre SSH pripojenie (POZOR: Pre produkčné prostredie použiť SSH kľúče!)
CENTRAL2_IP = "172.20.20.133"  # IP adresa zariadenia "Central2"
AZ2000_IP = "172.20.20.116"  # IP adresa zariadenia "AZ2000"
SSH_USER2 = "pi2"  # Používateľské meno pre SSH pripojenie k AZ2000
SSH_PASS2 = "otj0711"  # Heslo pre SSH pripojenie k AZ2000 (POZOR: Pre produkčné prostredie použiť SSH kľúče!)


class MainWindow(QtWidgets.QMainWindow):
    """
    Hlavné okno aplikácie pre ovládanie hvezdárne.
    """
    def __init__(self):
        """
        Inicializácia hlavného okna, nastavenie titulku, rozmerov a rozloženia.
        """
        super().__init__()  # Volanie konštruktora rodičovskej triedy
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - Version 25-3-2025 02")  # Nastavenie titulku okna
        self.setGeometry(100, 100, 800, 600)  # Nastavenie pozície a rozmerov okna

        # Hlavný layout - kontajner pre všetky ovládacie prvky v okne
        self.main_layout = QtWidgets.QWidget()  # Vytvorenie hlavného widgetu
        self.setCentralWidget(self.main_layout)  # Nastavenie hlavného widgetu pre okno
        self.grid_layout = QtWidgets.QGridLayout()  # Vytvorenie grid layoutu pre usporiadanie prvkov
        self.main_layout.setLayout(self.grid_layout)  # Priradenie grid layoutu hlavnému widgetu

        self.status_labels = {}  # Slovník pre uloženie labelov zobrazujúcich stav zásuviek

        # Logovacia sekcia - textové pole pre zobrazovanie správ a udalostí
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)  # Nastavenie textového poľa len na čítanie
        self.log_box.setMinimumHeight(100)  # Nastavenie minimálnej výšky textového poľa
        self.grid_layout.addWidget(self.log_box, 99, 0, 1, 2)  # Pridanie textového poľa do grid layoutu

        # Inicializácia sekcií - volanie metód pre vytvorenie jednotlivých častí ovládacieho rozhrania
        self.init_atacama_section()  # Inicializácia sekcie pre ovládanie ATACAMA
        self.init_wake_on_lan_section()  # Inicializácia sekcie pre Wake-on-LAN
        self.init_ota_section()  # Inicializácia sekcie pre OTA aktualizácie

        # Získanie počiatočného stavu zásuviek a spustenie časovača pre pravidelnú aktualizáciu
        self.aktualizuj_stav_zasuviek()  # Získanie a zobrazenie aktuálneho stavu zásuviek
        self.status_timer = QtCore.QTimer()  # Vytvorenie časovača pre pravidelné aktualizácie
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)  # Pripojenie funkcie k udalosti timeout
        self.status_timer.start(5 * 60 * 1000)  # Spustenie časovača, interval je 5 minút v milisekundách

    def aktualizuj_stav_zasuviek(self):
        """
        Získava a aktualizuje stav všetkých zásuviek.
        Táto metóda prechádza všetky definované zásuvky a zisťuje ich aktuálny stav pomocou externého programu.
        Výsledok je zobrazený v grafickom rozhraní pomocou LED indikátorov.
        """
        self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aktualizujem stav zásuviek.")
        for name, cislo in ZASUVKY.items():  # Prechádzanie slovníka so zásuvkami
            self.zisti_stav_zasuvky(cislo, name)  # Zistenie a zobrazenie stavu každej zásuvky

    def zisti_stav_zasuvky(self, cislo_zasuvky, label_name):
        """
        Zisťuje aktuálny stav danej zásuvky pomocou 'sispmctl -nqg'.

        Args:
            cislo_zasuvky (int): Číslo zásuvky, ktorej stav sa zisťuje.
            label_name (str): Názov labelu, ktorý zobrazuje stav zásuvky.
        """
        try:
            prikaz_stav = f"sispmctl -nqg {cislo_zasuvky}"  # Vytvorenie príkazu pre zistenie stavu
            vystup_stav = subprocess.check_output(prikaz_stav, shell=True, text=True).strip()  # Spustenie príkazu a získanie výstupu
            if vystup_stav == "1":  # Ak je zásuvka zapnutá
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_green.png"))  # Zobrazenie zelenej LED
            elif vystup_stav == "0":  # Ak je zásuvka vypnutá
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_red.png"))  # Zobrazenie červenej LED
            else:  # Ak je stav neznámy
                self.loguj(f"Neočakávaný výstup pre stav zásuvky {cislo_zasuvky}: '{vystup_stav}'")
                self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))  # Zobrazenie predvolenej LED
        except subprocess.CalledProcessError as e:  # Chyba pri vykonávaní príkazu
            self.loguj(f"Chyba pri zisťovaní stavu zásuvky {cislo_zasuvky}: {e}")
            self.status_labels[label_name].setPixmap(QtGui.QPixmap("led_def.png"))  # Zobrazenie predvolenej LED
        except FileNotFoundError:  # Ak program 'sispmctl' nie je nájdený
            self.loguj("Príkaz 'sispmctl' nebol nájdený. Nie je možné zistiť stav zásuviek.")
            for name in ZASUVKY:
                self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))  # Zobrazenie predvolenej LED pre všetky zásuvky

    def init_atacama_section(self):
        """
        Inicializuje sekciu ATACAMA v hlavnom okne.
        Táto sekcia obsahuje ovládacie prvky pre zásuvky, INDISTARTER a strechu.
        """
        group_box = QtWidgets.QGroupBox("ATACAMA")  # Vytvorenie group boxu pre zoskupenie súvisiacich prvkov
        layout = QtWidgets.QGridLayout()  # Vytvorenie grid layoutu pre usporiadanie prvkov v sekcii

        # Zásuvky - vytvorenie ovládacích prvkov pre každú zásuvku
        zasuvky_layout = QtWidgets.QGridLayout()
        zasuvky_group = QtWidgets.QGroupBox("Zásuvky")
        for i, (name, cislo) in enumerate(ZASUVKY.items()):  # Prechádzanie slovníka so zásuvkami
            label = QtWidgets.QLabel(name)  # Vytvorenie labelu s názvom zásuvky
            zapnut_button = QtWidgets.QPushButton("Zapnúť")  # Vytvorenie tlačidla pre zapnutie zásuvky
            vypnut_button = QtWidgets.QPushButton("Vypnúť")  # Vytvorenie tlačidla pre vypnutie zásuvky
            self.status_labels[name] = QtWidgets.QLabel()  # Vytvorenie labelu pre zobrazenie stavu zásuvky
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))  # Nastavenie predvolenej ikony LED
            zapnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))  # Pripojenie funkcie pre zapnutie
            vypnut_button.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))  # Pripojenie funkcie pre vypnutie
            zasuvky_layout.addWidget(label, i, 0)  # Pridanie labelu do layoutu
            zasuvky_layout.addWidget(zapnut_button, i, 1)  # Pridanie tlačidla pre zapnutie do layoutu
            zasuvky_layout.addWidget(vypnut_button, i, 2)  # Pridanie tlačidla pre vypnutie do layoutu
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))  # Nastavenie predvolenej ikony LED
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)  # Pridanie labelu pre stav do layoutu
        zasuvky_group.setLayout(zasuvky_layout)  # Nastavenie layoutu pre group box so zásuvkami
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)  # Pridanie group boxu do hlavného layoutu

        # INDISTARTER - tlačidlá pre spustenie programov INDISTARTER na rôznych zariadeniach
        indistarter_c14_button = QtWidgets.QPushButton("Spustiť INDISTARTER C14")
        indistarter_az2000_button = QtWidgets.QPushButton("Spustiť INDISTARTER AZ2000")
        indistarter_c14_button.clicked.connect(self.spusti_indistarter_c14)  # Pripojenie funkcie pre spustenie INDISTARTER na C14
        indistarter_az2000_button.clicked.connect(self.spusti_indistarter_az2000)  # Pripojenie funkcie pre spustenie INDISTARTER na AZ2000
        layout.addWidget(indistarter_c14_button, 1, 0, 1, 3)  # Pridanie tlačidla pre C14 do layoutu
        layout.addWidget(indistarter_az2000_button, 2, 0, 1, 3)  # Pridanie tlačidla pre AZ2000 do layoutu

        # Strecha - ovládacie prvky pre ovládanie strechy hvezdárne
        strecha_layout = QtWidgets.QGridLayout()
        strecha_group = QtWidgets.QGroupBox("Strecha")
        self.sever_button = QtWidgets.QPushButton("Sever")  # Tlačidlo pre posun strechy na sever
        self.juh_button = QtWidgets.QPushButton("Juh")  # Tlačidlo pre posun strechy na juh
        self.sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))  # Pripojenie funkcie pre posun na sever
        self.juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))  # Pripojenie funkcie pre posun na juh

        # Načasovanie strechy - ovládacie prvky pre nastavenie časovača pre automatický posun strechy
        self.casovac_strechy_group = QtWidgets.QGroupBox("Načasovať strechu")
        casovac_layout = QtWidgets.QGridLayout()
        self.casovac_strechy_enable = QtWidgets.QCheckBox("Aktivovať časovač")  # Checkbox pre aktiváciu/deaktiváciu časovača
        self.casovac_strechy_enable.stateChanged.connect(self.toggle_casovac_strechy)  # Pripojenie funkcie pre zmenu stavu checkboxu
        self.casovac_strechy_smer_label = QtWidgets.QLabel("Smer (sever/juh):")  # Label pre výber smeru posunu
        self.casovac_strechy_smer_combo = QtWidgets.QComboBox()  # Combo box pre výber smeru posunu
        self.casovac_strechy_smer_combo.addItem("sever")  # Pridanie možnosti "sever"
        self.casovac_strechy_smer_combo.addItem("juh")  # Pridanie možnosti "juh"
        self.casovac_strechy_cas_label = QtWidgets.QLabel("Čas (UTC HH:MM):")  # Label pre zadanie času
        self.casovac_strechy_cas_input = QtWidgets.QLineEdit()  # Pole pre zadanie času
        self.casovac_strechy_cas_input.setInputMask("HH:MM")  # Nastavenie masky pre formát času
        self.casovac_strechy_button = QtWidgets.QPushButton("Nastaviť časovač")  # Tlačidlo pre nastavenie časovača
        self.casovac_strechy_button.clicked.connect(self.nastav_casovac_strechy)  # Pripojenie funkcie pre nastavenie časovača
        self.casovac_strechy_button.setEnabled(False)  # Na začiatku je tlačidlo neaktívne

        casovac_layout.addWidget(self.casovac_strechy_enable, 0, 0, 1, 2)  # Pridanie checkboxu do layoutu
        casovac_layout.addWidget(self.casovac_strechy_smer_label, 1, 0)  # Pridanie labelu pre smer do layoutu
        casovac_layout.addWidget(self.casovac_strechy_smer_combo, 1, 1)  # Pridanie combo boxu pre smer do layoutu
        casovac_layout.addWidget(self.casovac_strechy_cas_label, 2, 0)  # Pridanie labelu pre čas do layoutu
        casovac_layout.addWidget(self.casovac_strechy_cas_input, 2, 1)  # Pridanie poľa pre čas do layoutu
        casovac_layout.addWidget(self.casovac_strechy_button, 3, 0, 1, 2)  # Pridanie tlačidla pre nastavenie časovača do layoutu
        self.casovac_strechy_group.setLayout(casovac_layout)  # Nastavenie layoutu pre group box s časovačom

        strecha_layout.addWidget(self.sever_button, 0, 0)  # Pridanie tlačidla pre sever do layoutu
        strecha_layout.addWidget(self.juh_button, 0, 1)  # Pridanie tlačidla pre juh do layoutu
        strecha_group.setLayout(strecha_layout)  # Nastavenie layoutu pre group box so strechou
        layout.addWidget(strecha_group, 3, 0, 1, 3)  # Pridanie group boxu pre strechu do hlavného layoutu
        layout.addWidget(self.casovac_strechy_group, 4, 0, 1, 3)  # Pridanie group boxu pre časovač do hlavného layoutu

        group_box.setLayout(layout)  # Nastavenie layoutu pre hlavný group box sekcie ATACAMA
        self.grid_layout.addWidget(group_box, 0, 0)  # Pridanie group boxu do hlavného grid layoutu

        # Inicializácia časovača pre načasovanú strechu
        self.strecha_casovac = QtCore.QTimer()  # Vytvorenie časovača
        self.strecha_casovac.timeout.connect(self.skontroluj_cas_strechy)  # Pripojenie funkcie pre kontrolu času
        self.strecha_casovac.start(60 * 1000)  # Spustenie časovača, interval je 1 minúta v milisekundách
        self.nacasovana_strecha_aktivna = False  # Príznak, či je časovač strechy aktívny
        self.nacasovany_smer_strechy = None  # Uložený smer posunu strechy
        self.nacasovany_cas_strechy_utc = None  # Uložený čas posunu strechy v UTC

    def toggle_casovac_strechy(self, state):
        """
        Povolí alebo zakáže ovládacie prvky pre časovač strechy.

        Args:
            state (int): Stav checkboxu (0 pre nezaškrtnutý, 2 pre zaškrtnutý).
        """
        enabled = (state == QtCore.Qt.Checked)  # Zistenie, či je checkbox zaškrtnutý
        self.casovac_strechy_smer_combo.setEnabled(enabled)  # Povolenie/zakázanie combo boxu pre smer
        self.casovac_strechy_cas_input.setEnabled(enabled)  # Povolenie/zakázanie poľa pre zadanie času
        self.casovac_strechy_button.setEnabled(enabled)  # Povolenie/zakázanie tlačidla pre nastavenie časovača
        if not enabled:  # Ak je časovač deaktivovaný
            self.nacasovana_strecha_aktivna = False  # Nastavenie príznaku na neaktívny
            self.nacasovany_smer_strechy = None  # Vymazanie uloženého smeru
            self.nacasovany_cas_strechy_utc = None  # Vymazanie uloženého času
            self.loguj("Časovač strechy bol deaktivovaný.")

    def nastav_casovac_strechy(self):
        """
        Nastaví časovač pre automatické ovládanie strechy na zadaný čas v UTC.
        Táto metóda načíta zadaný čas a smer posunu strechy, skontroluje jeho validitu
        a uloží ho pre neskoršie použitie časovačom.
        """
        smer = self.casovac_strechy_smer_combo.currentText().lower()  # Získanie smeru posunu z combo boxu
        cas_utc_str = self.casovac_strechy_cas_input.text()  # Získanie času posunu z textového poľa

        try:
            datetime.strptime(cas_utc_str, "%H:%M")  # Skontrolujeme, či je formát času správny
            self.nacasovana_strecha_aktivna = True  # Nastavenie príznaku, že je časovač aktívny
            self.nacasovany_smer_strechy = smer  # Uloženie smeru posunu
            self.nacasovany_cas_strechy_utc = cas_utc_str  # Uloženie času posunu ako reťazec
            self.loguj(f"Časovač strechy nastavený na {self.nacasovany_cas_strechy_utc} UTC ({self.nacasovany_smer_strechy}).")
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Chyba", "Nesprávny formát času (HH:MM). Zadajte čas v UTC.")

    def skontroluj_cas_strechy(self):
        """
        Pravidelne kontroluje, či nastal čas (v UTC) pre ovládanie strechy.
        Táto metóda sa spúšťa každú minútu a porovnáva aktuálny čas v UTC s uloženým časom.
        Ak sa časy zhodujú, vykoná sa posun strechy a časovač sa deaktivuje.
        """
        if self.nacasovana_strecha_aktivna and self.nacasovany_cas_strechy_utc:
            teraz_utc = datetime.now(pytz.utc).strftime("%H:%M")  # Získanie aktuálneho času v UTC
            if teraz_utc == self.nacasovany_cas_strechy_utc:  # Porovnanie aktuálneho času s uloženým časom
                self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Nastal čas (UTC) na ovládanie strechy na '{self.nacasovany_smer_strechy}'.")
                self.ovladaj_strechu(self.nacasovany_smer_strechy)  # Vykonanie posunu strechy
                self.nacasovana_strecha_aktivna = False  # Deaktivácia časovača
                self.casovac_strechy_enable.setChecked(False)  # Deaktivácia checkboxu v GUI
                QtWidgets.QMessageBox.information(self, "Časovač strechy",
                                                  f"Strecha bola presunutá na '{self.nacasovany_smer_strechy}' o {self.nacasovany_cas_strechy_utc} UTC. Časovač bol deaktivovaný.")

    def init_wake_on_lan_section(self):
        """
        Inicializuje sekciu WAKE-ON-LAN v hlavnom okne.
        Táto sekcia obsahuje tlačidlá pre prebudenie zariadení pomocou Wake-on-LAN.
        """
        group_box = QtWidgets.QGroupBox("WAKE-ON-LAN")  # Vytvorenie group boxu
        layout = QtWidgets.QGridLayout()  # Vytvorenie grid layoutu
        az2000_button = QtWidgets.QPushButton("Zapni AZ2000")  # Vytvorenie tlačidla pre zapnutie AZ2000
        gm3000_button = QtWidgets.QPushButton("Zapni GM3000")  # Vytvorenie tlačidla pre zapnutie GM3000
        az2000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))  # MAC adresa AZ2000
        gm3000_button.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))  # MAC adresa GM3000
        layout.addWidget(az2000_button, 0, 0)  # Pridanie tlačidla pre AZ2000 do layoutu
        layout.addWidget(gm3000_button, 0, 1)  # Pridanie tlačidla pre GM3000 do layoutu
        group_box.setLayout(layout)  # Nastavenie layoutu pre group box
        self.grid_layout.addWidget(group_box, 0, 1)  # Pridanie group boxu do hlavného grid layoutu

    def init_ota_section(self):
        """
        Inicializuje sekciu OTA Aktualizácie v hlavnom okne.
        Táto sekcia obsahuje tlačidlo pre spustenie aktualizácie programu.
        """
        group_box = QtWidgets.QGroupBox("OTA Aktualizácie")  # Vytvorenie group boxu
        layout = QtWidgets.QGridLayout()  # Vytvorenie grid layoutu
        aktualizovat_button = QtWidgets.QPushButton("Aktualizovať program")  # Vytvorenie tlačidla pre aktualizáciu
        aktualizovat_button.clicked.connect(self.aktualizuj_program)  # Pripojenie funkcie pre aktualizáciu
        layout.addWidget(aktualizovat_button, 0, 0)  # Pridanie tlačidla pre aktualizáciu do layoutu
        group_box.setLayout(layout)  # Nastavenie layoutu pre group box
        self.grid_layout.addWidget(group_box, 1, 0)  # Pridanie group boxu do hlavného grid layoutu

        # Pridanie linkov na kamery - zobrazenie odkazov na webové kamery
        kamera_atacama_label = QtWidgets.QLabel("<a href='http://172.20.20.134'>Kamera Atacama</a>")
        kamera_atacama_label.setOpenExternalLinks(True)  # Povolenie otvárania odkazov v prehliadači
        kamera_astrofoto_label = QtWidgets.QLabel("<a href='http://172.20.20.131'>Kamera Astrofoto</a>")
        kamera_astrofoto_label.setOpenExternalLinks(True)  # Povolenie otvárania odkazov v prehliadači
        self.grid_layout.addWidget(kamera_atacama_label, 1, 1)  # Pridanie labelu s odkazom na kameru Atacama
        self.grid_layout.addWidget(kamera_astrofoto_label, 2, 1)  # Pridanie labelu s odkazom na kameru Astrofoto

    def ovladaj_zasuvku(self, cislo_zasuvky, zapnut, label_name):
        """
        Ovláda zadanú zásuvku pomocou príkazu `sispmctl` a následne aktualizuje status.

        Args:
            cislo_zasuvky (int): Číslo zásuvky, ktorá sa má ovládať.
            zapnut (bool): True pre zapnutie, False pre vypnutie.
            label_name (str): Názov labelu, ktorý zobrazuje stav zásuvky.
        """
        prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"  # Vytvorenie príkazu pre ovládanie zásuvky
        try:
            vystup = subprocess.check_output(prikaz, shell=True)  # Spustenie príkazu
            self.loguj(vystup.decode())  # Zaznamenanie výsledku príkazu
            # Po úspešnom ovládaní zistíme aktuálny stav a aktualizujeme ikonu
            self.zisti_stav_zasuvky(cislo_zasuvky, label_name)
        except subprocess.CalledProcessError as e:  # Chyba pri vykonávaní príkazu
            self.loguj(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
            # Aj po neúspešnom ovládaní sa pokúsime zistiť aktuálny stav
            self.zisti_stav_zasuvky(cislo_zasuvky, label_name)

    def spusti_indistarter_c14(self):
        """
        Spustí príkaz `indistarter` na C14.
        Tento príkaz pravdepodobne spúšťa nejaký proces alebo službu na zariadení C14.
        """
        try:
            c14_prikaz = "indistarter"  # Príkaz na spustenie INDISTARTER
            c14_vystup = subprocess.check_output(c14_prikaz, shell=True)  # Spustenie príkazu a získanie výstupu
            self.loguj(f"INDISTARTER na C14: {c14_vystup.decode()}")  # Zaznamenanie výstupu
        except subprocess.CalledProcessError as e:  # Chyba pri vykonávaní príkazu
            self.loguj(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")

    def spusti_indistarter_az2000(self):
        """
        Spustí príkaz `indistarter` na UVEX-RPi (AZ2000) cez SSH.
        Táto metóda sa pripája k vzdialenému zariadeniu pomocou SSH a spúšťa tam príkaz.
        POZOR: Heslo je stále uložené v kóde, čo je bezpečnostné riziko. Pre produkčné prostredie
        sa odporúča použiť SSH kľúče.
        """
        try:
            uvex_prikaz = f"ssh {SSH_USER2}@{AZ2000_IP} indistarter"  # Príkaz pre spustenie INDISTARTER cez SSH
            uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True, text=True,
                                                  input=f"{SSH_PASS2}\n".encode())  # Spustenie príkazu a získanie výstupu, zadanie hesla cez input
            self.loguj(f"INDISTARTER na UVEX-RPi (AZ2000): {uvex_vystup.decode()}")  # Zaznamenanie výstupu
        except subprocess.CalledProcessError as e:  # Chyba pri vykonávaní príkazu
            self.loguj(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")
        except FileNotFoundError:  # Ak príkaz 'ssh' nie je nájdený
            self.loguj("Príkaz 'ssh' nebol nájdený.")

    def ovladaj_strechu(self, strana):
        """
        Ovláda strechu (sever/juh) pomocou príkazu `crelay`.
        Táto metóda ovláda motory strechy hvezdárne pomocou externého programu `crelay`.
        """
        if strana == "sever":
            prikaz1 = "crelay -s BITFT 2 ON"  # Príkaz pre posun na sever
            prikaz2 = "crelay -s BITFT 2 OFF"  # Príkaz pre vypnutie relé po posune na sever
        elif strana == "juh":
            prikaz1 = "crelay -s BITFT 1 ON"  # Príkaz pre posun na juh
            prikaz2 = "crelay -s BITFT 1 OFF"  # Príkaz pre vypnutie relé po posune na juh
        else:
            self.loguj("Neplatná strana strechy.")
            return

        try:
            subprocess.run(prikaz1, shell=True, check=True)  # Spustenie príkazu pre zapnutie relé
            time.sleep(2)  # Počkanie 2 sekundy (doba trvania posunu)
            subprocess.run(prikaz2, shell=True, check=True)  # Spustenie príkazu pre vypnutie relé
            self.loguj(f"Strecha ({strana}) ovládaná.")
        except subprocess.CalledProcessError as e:  # Chyba pri vykonávaní príkazu
            self.loguj(f"Chyba pri ovládaní strechy ({strana}): {e}")
        except FileNotFoundError:  # Ak príkaz 'crelay' nie je nájdený
            self.loguj("Príkaz 'crelay' nebol nájdený.")

    def wake_on_lan(self, mac_adresa):
        """
        Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN.
        Táto metóda používa knižnicu `wakeonlan` na odoslanie špeciálneho paketu, ktorý
        zariadenie dokáže prebudiť zo spánku alebo vypnutého stavu (ak je to podporované).

        Args:
            mac_adresa (str): MAC adresa zariadenia, ktoré sa má prebudiť.
        """
        self.loguj(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
        try:
            send_magic_packet(mac_adresa)  # Odoslanie magic packetu
        except Exception as e:  # Chyba pri odosielaní paketu
            self.loguj(f"Chyba pri odosielaní magic packetu: {e}")

    def aktualizuj_program(self):
        """
        Aktualizuje program z GitHub repozitára.
        Táto metóda stiahne novú verziu programu z GitHub repozitára a nahradí ňou
        aktuálnu verziu. Potom reštartuje aplikáciu.
        POZOR: Táto metóda predpokladá, že program je spúšťaný z prostredia, kde je
        nainštalovaný `curl` a má práva na zápis do adresára s programom.
        """
        try:
            # 1. Stiahnutie aktualizovaného súboru
            self.loguj("Aktualizujem program...")
            prikaz_stiahnutie = f"curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/refs/heads/main/C14/C14.py"
            subprocess.run(prikaz_stiahnutie, shell=True, check=True)

            # 2. Nahradenie existujúceho súboru
            prikaz_nahradenie = f"cp C14.py {PROGRAM_CESTA}"
            subprocess.run(prikaz_nahradenie, shell=True, check=True)

            # 3. Reštart aplikácie (ak je to potrebné) - zobrazí sa upozornenie pre používateľa
            self.loguj("Program bol aktualizovaný. Zavrite toto okno a otvorte program nanovo!!!!")
            pass  # Po aktualizácii je nutné program reštartovať ručne
        except subprocess.CalledProcessError as e:
            self.loguj(f"Chyba pri aktualizácii programu: {e}")
        except FileNotFoundError:
            self.loguj("Príkaz 'curl' alebo 'cp' nebol nájdený.")
        except Exception as e:
            self.loguj(f"Neočakávaná chyba: {e}")

    def loguj(self, sprava):
        """
        Zobrazí správu v logovacej sekcii.
        Táto metóda pridáva aktuálny čas a správu do textového poľa pre zobrazovanie logov.

        Args:
            sprava (str): Správa, ktorá sa má zobraziť.
        """
        cas = QtCore.QTime.currentTime().toString()  # Získanie aktuálneho času
        self.log_box.append(f"[{cas}] {sprava}")  # Pridanie správy s časom do textového poľa
        self.log_box.moveCursor(QtGui.QTextCursor.End)  # Posunutie kurzora na koniec textového poľa, aby bola nová správa viditeľná


if __name__ == "__main__":
    """
    Spustenie aplikácie.
    Táto časť kódu sa vykoná len v prípade, že je skript spustený priamo (nie importovaný).
    Vytvorí inštanciu aplikácie PyQt5 a hlavného okna a spustí event loop.
    """
    app = QtWidgets.QApplication(sys.argv)  # Vytvorenie inštancie aplikácie
    hlavne_okno = MainWindow()  # Vytvorenie inštancie hlavného okna
    hlavne_okno.show()  # Zobrazenie hlavného okna
    sys.exit(app.exec_())  # Spustenie event loopu aplikácie
