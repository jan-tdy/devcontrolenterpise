import tkinter as tk  # Importuje modul tkinter pre GUI
from tkinter import ttk, messagebox  # Importuje ttk pre moderný vzhľad a messagebox pre dialógové okná
import subprocess  # Importuje modul subprocess pre spúšťanie externých príkazov
import time  # Importuje modul time pre prácu s časom
import threading  # Importuje modul threading pre prácu s vláknami (používa sa implicitne, napr. pri aktualizácii GUI)
import os  # Importuje modul os pre prácu s operačným systémom
import socket  # Importuje modul socket pre sieťovú komunikáciu
import webbrowser # Importuje modul webbrowser pre otváranie webových stránok

# Konštanty - definície nemenných hodnôt pre zlepšenie čitateľnosti a údržby kódu
ZASUVKY = {  # Slovník priradzujúci názvy zásuviek ich číslam
    "NOUT": 4,
    "C14": 3,
    "RC16": 2,
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"  # Cesta k spustiteľnému súboru programu (možno bude potrebné zmeniť)
CONFIG_FILE = "az2000_config.txt"  # Názov konfiguračného súboru
# UPDATE_SCRIPT = "update_c14.sh"  # Skript pre aktualizáciu - PRESUNUTÉ DO KÓDU
# SEND_MAGIC_PACKET_SCRIPT = "/home/dpv/send_magic_packet.sh"  # Skript pre odosielanie magic packetov - ODSTRÁNENÉ

# Premenné pre konfiguráciu AZ2000 - predvolené hodnoty, ktoré sa načítajú z konfiguračného súboru
AZ2000_IP = "172.20.20.116"  # Predvolená IP adresa pre AZ2000
SSH_USER2 = "pi2"  # Predvolené používateľské meno pre SSH pripojenie k AZ2000
SSH_PASS2 = "otj0711"  # Predvolené heslo pre SSH pripojenie k AZ2000
GM3000_MAC = "00:c0:08:aa:35:12"  # MAC adresa pre GM3000

# Funkcie - definície funkcií pre logické rozdelenie kódu a znovupoužiteľnosť

def load_config():
    """
    Načíta konfiguráciu AZ2000 z konfiguračného súboru.
    Ak súbor neexistuje, použije predvolené hodnoty a vytvorí prázdny konfiguračný súbor.
    V prípade inej chyby pri čítaní súboru vypíše chybovú správu.
    """
    global AZ2000_IP, SSH_USER2, SSH_PASS2  # Používa globálne premenné, ktoré budú aktualizované
    try:
        with open(CONFIG_FILE, "r") as f:  # Otvorí konfiguračný súbor na čítanie
            lines = f.readlines()  # Načíta všetky riadky zo súboru
            if len(lines) >= 3:  # Kontroluje, či sú v súbore aspoň 3 riadky (IP, user, pass)
                AZ2000_IP = lines[0].strip()  # Načíta IP adresu a odstráni biele znaky z oboch strán
                SSH_USER2 = lines[1].strip()  # Načíta používateľské meno a odstráni biele znaky
                SSH_PASS2 = lines[2].strip()  # Načíta heslo a odstráni biele znaky
    except FileNotFoundError:  # Obslúži prípad, keď konfiguračný súbor neexistuje
        print("Konfiguračný súbor nebol nájdený. Používajú sa predvolené hodnoty.")
        # Vytvor prázdny konfiguračný súbor, aby sa predišlo opakovaným chybám pri ďalších pokusoch o načítanie
        try:
            with open(CONFIG_FILE, "w") as f:
                pass
        except Exception as e:
            print(f"Chyba pri vytváraní prázdneho konfiguračného súboru: {e}")
    except Exception as e:  # Obslúži ostatné výnimky, ktoré môžu nastať pri čítaní súboru
        print(f"Chyba pri načítaní konfigurácie: {e}")  # Vypíše chybovú správu s konkrétnou chybou

def save_config(ip, user, password):
    """
    Uloží konfiguráciu AZ2000 (IP adresa, používateľské meno, heslo) do konfiguračného súboru.
    V prípade úspešného uloženia vráti True, inak vráti False a vypíše chybovú správu.
    """
    try:
        with open(CONFIG_FILE, "w") as f:  # Otvorí konfiguračný súbor na zápis (prepíše jeho obsah)
            f.write(f"{ip}\n")  # Zapíše IP adresu a prejde na nový riadok
            f.write(f"{user}\n")  # Zapíše používateľské meno a prejde na nový riadok
            f.write(f"{password}\n")  # Zapíše heslo a prejde na nový riadok
        print("Konfigurácia AZ2000 bola uložená.")  # Potvrdí úspešné uloženie
        return True  # Vráti True pri úspechu
    except Exception as e:  # Obslúži prípadnú výnimku počas zápisu do súboru
        print(f"Chyba pri ukladaní konfigurácie: {e}")  # Vypíše chybovú správu s konkrétnou chybou
        return False  # Vráti False pri chybe

def ovladaj_zasuvku(cislo_zasuvky, zapnut, label_name):
    """
    Ovláda zadanú zásuvku (zapnutie alebo vypnutie) pomocou externého príkazu `sispmctl`.
    Aktualizuje farbu LEDky v GUI na zeleno pri zapnutí, červeno pri vypnutí a šedo pri chybe.

    Parametre:
    cislo_zasuvky (int): Číslo zásuvky, ktorá sa má ovládať.
    zapnut (bool): True pre zapnutie, False pre vypnutie.
    label_name (ttk.Label): Objekt Labelu z GUI, ktorý reprezentuje LEDku pre danú zásuvku.
    """
    prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"  # Zostaví príkaz pre `sispmctl`
    try:
        vystup = subprocess.check_output(prikaz, shell=True)  # Spustí príkaz v shelli a zachytí výstup
        print(vystup.decode())  # Dekóduje a vypíše výstup príkazu
        if zapnut:
            label_name.config(bg="green")  # Nastaví pozadie Labelu na zeleno pre zapnutý stav
        else:
            label_name.config(bg="red")  # Nastaví pozadie Labelu na červeno pre vypnutý stav
    except subprocess.CalledProcessError as e:  # Obslúži chybu, ak príkaz `sispmctl` zlyhá
        print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")  # Vypíše chybovú správu
        label_name.config(bg="gray")  # Nastaví pozadie Labelu na šedo pre indikáciu chyby

def spusti_indistarter_c14():
    """
    Spustí príkaz `indistarter` na lokálnom počítači (C14).
    Tento príkaz pravdepodobne spúšťa nejakú inú aplikáciu alebo službu.
    """
    try:
        c14_prikaz = "indistarter"  # Príkaz na spustenie (pravdepodobne lokálnej) aplikácie
        c14_vystup = subprocess.check_output(c14_prikaz, shell=True)  # Spustí príkaz a zachytí výstup
        print(f"INDISTARTER na C14: {c14_vystup.decode()}")  # Vypíše výstup príkazu
    except subprocess.CalledProcessError as e:  # Obslúži chybu, ak príkaz zlyhá
        print(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")  # Vypíše chybovú správu

def spusti_indistarter_az2000():
    """
    Spustí príkaz `indistarter` na vzdialenom počítači (AZ2000) cez SSH pripojenie.
    Používa `sshpass` pre zadanie hesla neinteraktívne (POZOR: Bezpečné len v obmedzených prípadoch!).
    """
    global AZ2000_IP, SSH_USER2, SSH_PASS2  # Používa globálne premenné pre pripojenie k AZ2000
    try:
        uvex_prikaz = f"sshpass -p '{SSH_PASS2}' ssh -o StrictHostKeyChecking=no {SSH_USER2}@{AZ2000_IP} 'indistarter'"  # Príkaz pre spustenie indistarter cez SSH
        subprocess.run(uvex_prikaz, shell=True, check=True)  # Spustí príkaz cez shell a kontroluje návratový kód
        print(f"INDISTARTER na UVEX-RPi (AZ2000) spustený.")  # Potvrdí úspešné spustenie
    except subprocess.CalledProcessError as e:  # Obslúži chybu, ak príkaz zlyhá
        print(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")  # Vypíše chybovú správu

def ovladaj_strechu(strana):
    """
    Ovláda strechu (sever alebo juh) pomocou externého príkazu `crelay`.
    Spustí dva príkazy pre otvorenie a zatvorenie strechy pre zadanú stranu.
    """
    if strana == "sever":  # Ak je strana sever
        prikaz1 = "crelay -s BITFT 2 ON"  # Príkaz pre otvorenie severnej časti strechy
        prikaz2 = "crelay -s BITFT 2 OFF"  # Príkaz pre zatvorenie severnej časti strechy
    elif strana == "juh":  # Ak je strana juh
        prikaz1 = "crelay -s BITFT 1 ON"  # Príkaz pre otvorenie južnej časti strechy
        prikaz2 = "crelay -s BITFT 1 OFF"  # Príkaz pre zatvorenie južnej časti strechy
    else:  # Ak je zadaná neplatná strana
        print("Neplatná strana strechy.")  # Vypíše chybovú správu
        return  # Ukončí funkciu

    try:
        subprocess.run(prikaz1, shell=True, check=True)  # Spustí prvý príkaz a kontroluje návratový kód
        time.sleep(2)  # Počká 2 sekundy (kvôli mechanike strechy)
        subprocess.run(prikaz2, shell=True, check=True)  # Spustí druhý príkaz a kontroluje návratový kód
        print(f"Strecha ({strana}) ovládaná.")  # Potvrdí úspešné ovládanie strechy
    except subprocess.CalledProcessError as e:  # Obslúži chybu, ak niektorý z príkazov zlyhá
        print(f"Chyba pri ovládaní strechy ({strana}): {e}")  # Vypíše chybovú správu

def wake_on_lan(mac_adresa):
    """
    Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN.
    Nahrádza volanie externého skriptu priamym kódom v Pythone.

    Parameter:
    mac_adresa (str): MAC adresa zariadenia, ktoré sa má prebudiť (napr. "00:11:22:33:44:55").
    """
    print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
    try:
        mac_bytes = bytes.fromhex(mac_adresa.replace(':', ''))  # Prekonvertuje MAC adresu na bajty, odstráni ':'
        packet = b'\xff' * 6 + mac_bytes * 16  # Vytvorí magic packet: 6x FF + 16x MAC adresa
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:  # Vytvorí UDP socket
            s.sendto(packet, ('<broadcast>', 9))  # Odošle packet na broadcast adresu a port 9 (štandardný WOL port)
        print("Magic packet odoslaný.")  # Potvrdí odoslanie packetu
    except Exception as e:  # Obslúži prípadné výnimky (napr. neplatná MAC adresa, problém so socketom)
        print(f"Chyba pri odosielaní magic packetu: {e}")  # Vypíše chybovú správu
        messagebox.showerror("Chyba", f"Chyba pri odosielaní WOL paketu: {e}")  # Zobrazí chybové okno

def aktualizuj_program():
    """
    Aktualizuje program z GitHub repozitára.
    Implementované priamo v Pythone namiesto volania externého skriptu.
    Zastaví bežiaci program, stiahne novú verziu a reštartuje aplikáciu.
    """
    try:
        print("Aktualizujem program...")
        # 1. Zastavíme bežiaci program.
        prikaz_zastavenie = "pkill -f 'python3 /home/dpv/j44softapps-socketcontrol/C14.py'"  # Príkaz na zastavenie skriptu
        subprocess.run(prikaz_zastavenie, shell=True, check=False)  # Spustí príkaz, check=False ignoruje chybu, ak program nebeží

        # 2. Prejdeme do správneho adresára.
        os.chdir("/home/dpv/j44softapps-socketcontrol/")  # Zmení aktuálny pracovný adresár

        # 3. Stiahneme najnovšiu verziu skriptu.
        url = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py"  # URL adresa novej verzie skriptu
        prikaz_stiahnutie = f"curl -O {url}"  # Príkaz na stiahnutie súboru pomocou curl
        subprocess.run(prikaz_stiahnutie, shell=True, check=True)  # Spustí príkaz a kontroluje návratový kód

        print("Stiahnutá nová verzia programu.")  # Potvrdí stiahnutie novej verzie

        # 4. Reštartujeme program.
        prikaz_restart = "python3 /home/dpv/j44softapps-socketcontrol/C14.py &"  # Príkaz na reštart skriptu na pozadí (&)
        subprocess.Popen(prikaz_restart, shell=True, close_fds=True)  # Spustí príkaz na pozadí a uvoľní deskriptory súborov
        print("Program reštartovaný na pozadí.")  # Potvrdí reštart
        root.destroy()  # Ukončí Tkinter aplikáciu (hlavné okno)
    except Exception as e:  # Obslúži prípadné výnimky počas aktualizácie
        print(f"Chyba pri aktualizácii: {e}")  # Vypíše chybovú správu
        messagebox.showerror("Chyba", f"Chyba pri aktualizácii: {e}")  # Zobrazí chybové okno

# Triedy - definície tried pre štruktúrovaný kód a objektovo orientovaný prístup

class MainWindow(tk.Tk):
    """
    Hlavné okno aplikácie, dedí od tk.Tk (základné okno Tkinter).
    Vytvára a spravuje všetky GUI elementy (widgety) a ich rozloženie.
    """
    def __init__(self):
        super().__init__()  # Volá konštruktor rodičovskej triedy (tk.Tk)
        self.title("Ovládanie Hvezdárne - C14 - Tkinter verzia")  # Nastaví titulok okna
        self.geometry("800x600")  # Nastaví počiatočnú veľkosť okna
        self.configure(padx=10, pady=10)  # Nastaví vnútorné okraje okna

        load_config()  # Načíta konfiguráciu zo súboru pri spustení aplikácie

        grid = ttk.Frame(self)  # Vytvorí hlavný grid layout manager
        grid.pack(fill="both", expand=True)  # Rozšíri grid na celé okno
        grid.columnconfigure(0, weight=1)  # Nastaví stĺpce a riadky na roztiahnutie
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)
        grid.columnconfigure(3, weight=1)
        grid.rowconfigure(0, weight=1)

        # ATACAMA sekcia - rám a grid pre ovládanie Atacamy
        atacama_frame = ttk.LabelFrame(grid, text="ATACAMA")  # Rám s popisom
        atacama_frame.grid(row=0, column=0, columnspan=1, sticky="nsew", padx=5, pady=5)  # Umiestnenie v hlavnom grid-e

        atacama_grid = ttk.Frame(atacama_frame)  # Grid pre widgety v rámci Atacama sekcie
        atacama_grid.pack(fill="both", expand=True)
        atacama_grid.columnconfigure(0, weight=1)  # Nastavenie roztiahnutia pre vnútorný grid
        atacama_grid.columnconfigure(1, weight=1)
        atacama_grid.columnconfigure(2, weight=1)
        atacama_grid.columnconfigure(3, weight=1)
        atacama_grid.rowconfigure(0, weight=1)

        # Zásuvky - rám a grid pre ovládanie zásuviek
        zasuvky_frame = ttk.LabelFrame(atacama_grid, text="Zásuvky")  # Rám pre zásuvky
        zasuvky_frame.grid(row=0, column=0, columnspan=1, sticky="nsew", padx=5, pady=5)  # Umiestnenie v Atacama grid-e

        zasuvky_grid = ttk.Frame(zasuvky_frame)  # Grid pre widgety ovládania zásuviek
        zasuvky_grid.pack(fill="both", expand=True)
        for i, (name, cislo) in enumerate(ZASUVKY.items()):  # Prechádza cez definované zásuvky
            label = ttk.Label(zasuvky_grid, text=name)  # Vytvorí Label s názvom zásuvky
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")  # Umiestni Label do grid-u
            zapnut_button = ttk.Button(zasuvky_grid, text="Zapnúť",  # Vytvorí tlačidlo pre zapnutie
                                       command=lambda n=cislo, l=label: ovladaj_zasuvku(n, True, l))  # Priradí príkaz
            zapnut_button.grid(row=1, column=i, padx=5, pady=5, sticky="w")  # Umiestni tlačidlo
            vypnut_button = ttk.Button(zasuvky_grid, text="Vypnúť",  # Vytvorí tlačidlo pre vypnutie
                                       command=lambda n=cislo, l=label: ovladaj_zasuvku(n, False, l))  # Priradí príkaz
            vypnut_button.grid(row=2, column=i, padx=5, pady=5, sticky="w")  # Umiestni tlačidlo
            label.config(bg="gray")  # Nastaví počiatočnú farbu LEDky (Labelu)
            label.grid(row=3, column=i, padx=5, pady=5, sticky="w")  # Umiestni Label pre LEDku

        # INDISTARTER - tlačidlá pre spustenie INDISTARTER aplikácií
        indistarter_c14_button = ttk.Button(atacama_grid, text="Spustiť INDISTARTER C14", command=spusti_indistarter_c14)
        indistarter_c14_button.grid(row=0, column=1, columnspan=1, padx=5, pady=5, sticky="nsew")
        indistarter_az2000_button = ttk.Button(atacama_grid, text="Spustiť INDISTARTER AZ2000", command=spusti_indistarter_az2000)
        indistarter_az2000_button.grid(row=0, column=2, columnspan=1, padx=5, pady=5, sticky="nsew")

        # Strecha - rám a tlačidlá pre ovládanie strechy
        strecha_frame = ttk.LabelFrame(atacama_grid, text="Strecha")  # Rám pre ovládanie strechy
        strecha_frame.grid(row=0, column=3, columnspan=1, sticky="nsew", padx=5, pady=5)  # Umiestnenie v Atacama grid-e
        strecha_grid = ttk.Frame(strecha_frame)  # Grid pre tlačidlá ovládania strechy
        strecha_grid.pack(fill="both", expand=True)
        sever_button = ttk.Button(strecha_grid, text="Sever", command=lambda: ovladaj_strechu("sever"))  # Tlačidlo pre sever
        sever_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")  # Umiestnenie
        juh_button = ttk.Button(strecha_grid, text="Juh", command=lambda: ovladaj_strechu("juh"))  # Tlačidlo pre juh
        juh_button.grid(row=1, column=0, padx=5, pady=5, sticky="w")  # Umiestnenie

        # WAKE-ON-LAN sekcia - rám a tlačidlá pre prebudenie zariadení
        wake_frame = ttk.LabelFrame(grid, text="WAKE-ON-LAN")  # Rám pre WOL
        wake_frame.grid(row=0, column=1, columnspan=1, sticky="nsew", padx=5, pady=5)  # Umiestnenie v hlavnom grid-e
        wake_grid = ttk.Frame(wake_frame)  # Grid pre tlačidlá WOL
        wake_grid.pack(fill="both", expand=True)
        az2000_button = ttk.Button(wake_grid, text="Zapni AZ2000", command=lambda: wake_on_lan("00:c0:08:a9:c2:32"))  # Tlačidlo pre AZ2000
        az2000_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")  # Umiestnenie
        gm3000_button = ttk.Button(wake_grid, text="Zapni GM3000", command=lambda: wake_on_lan(GM3000_MAC))  # Tlačidlo pre GM3000
        gm3000_button.grid(row=1, column=0, padx=5, pady=5, sticky="w")  # Umiestnenie

        # OTA Aktualizácie sekcia - rám a tlačidlá pre aktualizáciu programu
        ota_frame = ttk.LabelFrame(grid, text="OTA Aktualizácie")  # Rám pre OTA aktualizácie
        ota_frame.grid(row=0, column=2, columnspan=1, sticky="nsew", padx=5, pady=5)  # Umiestnenie v hlavnom grid-eota_grid = ttk.Frame(ota_frame)  # Grid pre tlačidlá aktualizácie
        ota_grid.pack(fill="both", expand=True)
        aktualizovat_button = ttk.Button(ota_grid, text="Aktualizovať program", command=aktualizuj_program)  # Tlačidlo pre aktualizáciu
        aktualizovat_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")  # Umiestnenie

        # Kamery - Label pre zobrazenie odkazov na webkamery
        kamera_atacama_label = ttk.Label(ota_grid, text='<a href="http://172.20.20.134">Kamera Atacama</a>', cursor="hand2")
        kamera_atacama_label.bind("<Button-1>", lambda e: webbrowser.open_new("http://172.20.20.134"))
        kamera_atacama_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        kamera_astrofoto_label = ttk.Label(ota_grid, text='<a href="http://172.20.20.131">Kamera Astrofoto</a>', cursor="hand2")
        kamera_astrofoto_label.bind("<Button-1>", lambda e: webbrowser.open_new("http://172.20.20.131"))
        kamera_astrofoto_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Konfig sekcia - rám a prvky pre konfiguráciu AZ2000
        config_frame = ttk.LabelFrame(grid, text="Konfigurácia AZ2000")  # Rám pre konfiguráciu
        config_frame.grid(row=0, column=3, columnspan=1, sticky="nsew", padx=5, pady=5)  # Umiestnenie v hlavnom grid-e
        config_grid = ttk.Frame(config_frame)  # Grid pre prvky konfigurácie
        config_grid.pack(fill="both", expand=True)

        ip_label = ttk.Label(config_grid, text="IP adresa:")  # Label pre IP adresu
        ip_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")  # Umiestnenie
        self.ip_input = ttk.Entry(config_grid)  # Vstupný prvok pre IP adresu
        self.ip_input.insert(0, AZ2000_IP)  # Predvyplnenie aktuálnou hodnotou
        self.ip_input.grid(row=1, column=0, padx=5, pady=5, sticky="w")  # Umiestnenie

        user_label = ttk.Label(config_grid, text="SSH používateľ:")  # Label pre používateľské meno
        user_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")  # Umiestnenie
        self.user_input = ttk.Entry(config_grid)  # Vstupný prvok pre používateľské meno
        self.user_input.insert(0, SSH_USER2)  # Predvyplnenie
        self.user_input.grid(row=1, column=1, padx=5, pady=5, sticky="w")  # Umiestnenie

        password_label = ttk.Label(config_grid, text="SSH heslo:")  # Label pre heslo
        password_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")  # Umiestnenie
        self.password_input = ttk.Entry(config_grid, show="*")  # Vstupný prvok pre heslo (skryté zadávanie)
        self.password_input.insert(0, SSH_PASS2)  # Predvyplnenie
        self.password_input.grid(row=1, column=2, padx=5, pady=5, sticky="w")  # Umiestnenie

        save_button = ttk.Button(config_grid, text="Uložiť nastavenia", command=self.save_config)  # Tlačidlo pre uloženie konfigurácie
        save_button.grid(row=0, column=3, rowspan=2, padx=5, pady=5, sticky="nsew")  # Umiestnenie a roztiahnutie

    def save_config(self):
        """
        Uloží konfiguráciu AZ2000 (IP adresa, používateľské meno, heslo) do konfiguračného súboru.
        Zobrazí informačné alebo chybové okno v závislosti od výsledku uloženia.
        Aktualizuje globálne premenné s novými hodnotami.
        """
        global AZ2000_IP, SSH_USER2, SSH_PASS2  # Používa globálne premenné
        ip = self.ip_input.get()  # Získa hodnotu zadanú do vstupného poľa pre IP adresu
        user = self.user_input.get()  # Získa hodnotu zadanú do vstupného poľa pre používateľské meno
        password = self.password_input.get()  # Získa hodnotu zadanú do vstupného poľa pre heslo
        if save_config(ip, user, password):  # Volá funkciu pre uloženie konfigurácie do súboru
            messagebox.showinfo("Info", "Konfigurácia AZ2000 bola uložená.")  # Zobrazí informačné okno
            AZ2000_IP = ip  # Aktualizuje globálne premenné novými hodnotami
            SSH_USER2 = user
            SSH_PASS2 = password
        else:
            messagebox.showerror("Chyba", "Chyba pri ukladaní konfigurácie.")  # Zobrazí chybové okno pri chybe

# Spúšťací kód - vykoná sa pri spustení skriptu
if __name__ == "__main__":
    import webbrowser # Import pre funkciu prehliadania webu
    root = MainWindow()  # Vytvorí inštanciu hlavného okna
    root.mainloop()  # Spustí hlavný cyklus Tkinter aplikácie (zobrazí okno a reaguje na udalosti)
