import sys  # Importuje modul sys pre prácu so systémovými premennými a funkciami.
import subprocess  # Importuje modul subprocess pre spúšťanie externých príkazov.
import time  # Importuje modul time pre prácu s časom.
import gi  # Importuje modul gi, ktorý je základom pre knižnicu PyGObject.
import threading # Importuje modul threading pre prácu s vláknami
import os # Importuje modul os pre prácu s operačným systémom
import socket # Importuje modul socket pre prácu so sieťovými socketmi

gi.require_version("Gtk", "4.0")  # Požaduje verziu 4.0 knižnice Gtk.
from gi.repository import Gtk, GLib  # Importuje triedy Gtk a GLib z gi.repository.

# Konštanty
ZASUVKY = {  # Slovník definujúci názvy a čísla zásuviek.
    "NOUT": 4,
    "C14": 3,
    "RC16": 2,
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"  # Cesta k spustiteľnému súboru programu.
CONFIG_FILE = "az2000_config.txt"  # Konfiguračný súbor
# UPDATE_SCRIPT = "update_c14.sh"  # Skript pre aktualizáciu - PRESUNUTÉ DO KÓDU
# SEND_MAGIC_PACKET_SCRIPT = "/home/dpv/send_magic_packet.sh"  # Skript pre odosielanie magic packetov - ODSTRÁNENÉ

# Premenné pre konfiguráciu AZ2000 (predvolené hodnoty)
AZ2000_IP = "172.20.20.116"  # Predvolená IP adresa pre AZ2000.
SSH_USER2 = "pi2"  # Predvolené používateľské meno pre SSH pripojenie k AZ2000.
SSH_PASS2 = "otj0711"  # Predvolené heslo pre SSH pripojenie k AZ2000.
GM3000_MAC = "00:c0:08:aa:35:12"  # MAC adresa pre GM3000


def load_config():
    """Načíta konfiguráciu AZ2000 z konfiguračného súboru."""
    global AZ2000_IP, SSH_USER2, SSH_PASS2  # Používa globálne premenné.
    try:
        with open(CONFIG_FILE, "r") as f:  # Otvorí konfiguračný súbor na čítanie.
            lines = f.readlines()  # Načíta riadky zo súboru.
            if len(lines) >= 3:  # Kontroluje, či sú v súbore aspoň 3 riadky.
                AZ2000_IP = lines[0].strip()  # Načíta a otrimuje IP adresu.
                SSH_USER2 = lines[1].strip()  # Načíta a otrimuje používateľské meno.
                SSH_PASS2 = lines[2].strip()  # Načíta a otrimuje heslo.
    except FileNotFoundError:  # Obsluhuje prípad, keď konfiguračný súbor neexistuje.
        print("Konfiguračný súbor nebol nájdený. Používajú sa predvolené hodnoty.")
        # Vytvor prázdny konfiguračný súbor, aby sa predišlo opakovaným chybám pri ďalších pokusoch o načítanie
        try:
            with open(CONFIG_FILE, "w") as f:
                pass
        except Exception as e:
            print(f"Chyba pri vytváraní prázdneho konfiguračného súboru: {e}")
    except Exception as e:  # Obsluhuje ostatné výnimky pri čítaní súboru.
        print(f"Chyba pri načítaní konfigurácie: {e}")



def save_config(ip, user, password):
    """Uloží konfiguráciu AZ2000 do konfiguračného súboru."""
    try:
        with open(CONFIG_FILE, "w") as f:  # Otvorí konfiguračný súbor na zápis.
            f.write(f"{ip}\n")  # Zapisuje IP adresu.
            f.write(f"{user}\n")  # Zapisuje používateľské meno.
            f.write(f"{password}\n")  # Zapisuje heslo.
        print("Konfigurácia AZ2000 bola uložená.")
        return True
    except Exception as e:  # Obsluhuje výnimky pri zápise do súboru.
        print(f"Chyba pri ukladaní konfigurácie: {e}")
        return False



def ovladaj_zasuvku(cislo_zasuvky, zapnut, label_name):
    """Ovláda zadanú zásuvku pomocou príkazu `sispmctl`."""
    prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"  # Vytvorí príkaz pre `sispmctl`.
    try:
        vystup = subprocess.check_output(prikaz, shell=True)  # Spustí príkaz a získa výstup.
        print(vystup.decode())  # Dekóduje a vypíše výstup.
        GLib.idle_add(set_led_status, label_name, "green" if zapnut else "red")  # Aktualizuje LED v GUI.
    except subprocess.CalledProcessError as e:  # Obsluhuje chyby pri spúšťaní príkazu.
        print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
        GLib.idle_add(set_led_status, label_name, "def")  # Nastaví LED na predvolenú farbu pri chybe.



def spusti_indistarter_c14():
    """Spustí príkaz `indistarter` na C14."""
    try:
        c14_prikaz = "indistarter"  # Príkaz na spustenie indistarter
        c14_vystup = subprocess.check_output(c14_prikaz, shell=True)  # Spustí príkaz a získa výstup
        print(f"INDISTARTER na C14: {c14_vystup.decode()}")  # Vypíše výstup
    except subprocess.CalledProcessError as e:  # Obslúži chybu pri spustení príkazu
        print(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")



def spusti_indistarter_az2000():
    """Spustí príkaz `indistarter` na UVEX-RPi (AZ2000) cez SSH."""
    global AZ2000_IP, SSH_USER2, SSH_PASS2  # Používa globálne premenné pre pripojenie k AZ2000
    try:
        uvex_prikaz = f"sshpass -p '{SSH_PASS2}' ssh -o StrictHostKeyChecking=no {SSH_USER2}@{AZ2000_IP} 'indistarter'"  # Príkaz pre spustenie indistarter cez SSH
        subprocess.run(uvex_prikaz, shell=True, check=True)  # Spustí príkaz cez shell
        print(f"INDISTARTER na UVEX-RPi (AZ2000) spustený.")
    except subprocess.CalledProcessError as e:  # Obslúži chybu pri spustení príkazu
        print(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")



def ovladaj_strechu(strana):
    """Ovláda strechu (sever/juh) pomocou príkazu `crelay`."""
    if strana == "sever":  # Ak je strana sever
        prikaz1 = "crelay -s BITFT 2 ON"
        prikaz2 = "crelay -s BITFT 2 OFF"
    elif strana == "juh":  # Ak je strana juh
        prikaz1 = "crelay -s BITFT 1 ON"
        prikaz2 = "crelay -s BITFT 1 OFF"
    else:
        print("Neplatná strana strechy.")
        return

    try:
        subprocess.run(prikaz1, shell=True, check=True)  # Spustí prvý príkaz
        time.sleep(2)  # Počká 2 sekundy
        subprocess.run(prikaz2, shell=True, check=True)  # Spustí druhý príkaz
        print(f"Strecha ({strana}) ovládaná.")
    except subprocess.CalledProcessError as e:  # Obslúži chybu pri spustení príkazu
        print(f"Chyba pri ovládaní strechy ({strana}): {e}")



def wake_on_lan(mac_adresa):
    """Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN."""
    print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
    # Nahradzujeme volanie externého skriptu priamym kódom
    try:
        mac_bytes = bytes.fromhex(mac_adresa.replace(':', ''))  # Prekonvertuje MAC adresu na bajty
        packet = b'\xff' * 6 + mac_bytes * 16  # Vytvorí magic packet
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:  # Vytvorí UDP socket
            s.sendto(packet, ('<broadcast>', 9))  # Odošle packet na broadcast adresu
        print("Magic packet odoslaný.")
    except Exception as e:
        print(f"Chyba pri odosielaní magic packetu: {e}")
        show_error_dialog(f"Chyba pri odosielaní WOL paketu: {e}")



def aktualizuj_program():
    """Aktualizuje program z GitHub repozitára. Implementované priamo v Pythone."""
    try:
        print("Aktualizujem program...")
        # 1. Zastavíme bežiaci program.
        prikaz_zastavenie = "pkill -f 'python3 /home/dpv/j44softapps-socketcontrol/C14.py'"
        subprocess.run(prikaz_zastavenie, shell=True, check=False)  # check=False, aby nehodilo chybu, ak program nebeží

        # 2. Prejdeme do správneho adresára.
        os.chdir("/home/dpv/j44softapps-socketcontrol/")

        # 3. Stiahneme najnovšiu verziu skriptu.
        url = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py"
        prikaz_stiahnutie = f"curl -O {url}"
        subprocess.run(prikaz_stiahnutie, shell=True, check=True)
        print("Stiahnutá nová verzia programu.")

        # 4. Reštartujeme program.
        prikaz_restart = "python3 /home/dpv/j44softapps-socketcontrol/C14.py &"
        subprocess.Popen(prikaz_restart, shell=True, close_fds=True)  # Používame Popen pre reštart na pozadí
        print("Program reštartovaný na pozadí.")
        GLib.idle_add(Gtk.main_quit)  # Ukončíme GTK aplikáciu
    except Exception as e:
        print(f"Chyba pri aktualizácii: {e}")
        show_error_dialog(f"Chyba pri aktualizácii: {e}")



def set_led_status(label_name, farba):
    """Nastaví farbu LEDky v GUI pomocou CSS štýlov."""
    label = status_labels[label_name]  # Získa Label objekt zo slovníka status_labels
    if farba == "green":
        label.set_markup('<span foreground="green">●</span>')  # Nastaví zelenú farbu
    elif farba == "red":
        label.set_markup('<span foreground="red">●</span>')  # Nastaví červenú farbu
    else:
        label.set_markup('<span foreground="gray">●</span>')  # Alebo inú predvolenú farbu



def show_error_dialog(message):
    """Zobrazí chybový dialóg."""
    dialog = Gtk.MessageDialog(
        parent=None,  # Parent okno môže byť None, ak nemáme hlavné okno
        flags=Gtk.DialogFlags.MODAL,  # Dialóg je modálny
        message_type=Gtk.MessageType.ERROR,  # Typ správy je ERROR
        buttons=Gtk.ButtonsType.OK,  # Tlačidlo OK
        text=message,  # Text správy
    )
    dialog.run()  # Spustí dialóg
    dialog.destroy()  # Zničí dialóg po zatvorení



class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ovládanie Hvezdárne - C14 - GTK 4 verzia")  # Volá konštruktor rodičovskej triedy
        self.set_default_size(800, 600)  # Nastaví predvolenú veľkosť okna
        self.margin_start = 10
        self.margin_end = 10
        self.margin_top = 10
        self.margin_bottom = 10

        load_config()  # Načíta konfiguráciu zo súboru

        grid = Gtk.Grid()  # Vytvorí Grid layout manager
        grid.set_column_spacing(10)  # Nastaví medzery medzi stĺpcami
        grid.set_row_spacing(10)  # Nastaví medzery medzi riadkami
        self.set_child(grid)  # Nastaví Grid ako hlavný kontajner okna

        # ATACAMA sekcia
        atacama_frame = Gtk.Frame()
        atacama_frame_label = Gtk.Label(label="ATACAMA")  # Vytvoríme Label pre text
        atacama_frame.set_label_widget(atacama_frame_label)  # Nastavíme Label ako widget labelu rámčeka
        atacama_grid = Gtk.Grid()
        atacama_grid.set_column_spacing(5)
        atacama_grid.set_row_spacing(5)
        atacama_frame.set_child(atacama_grid)
        grid.attach(atacama_frame, 0, 0, 1, 1)

        # Zásuvky
        zasuvky_frame = Gtk.Frame()
        zasuvky_frame_label = Gtk.Label(label="Zásuvky")
        zasuvky_frame.set_label_widget(zasuvky_frame_label)
        zasuvky_grid = Gtk.Grid()
        zasuvky_grid.set_column_spacing(5)
        zasuvky_grid.set_row_spacing(5)
        zasuvky_frame.set_child(zasuvky_grid)
        atacama_grid.attach(zasuvky_frame, 0, 0, 1, 1)

        global status_labels  # Používa globálny slovník pre ukladanie Label objektov
        status_labels = {}
        for i, (name, cislo) in enumerate(ZASUVKY.items()):  # Prechádza cez zásuvky
            label = Gtk.Label(label=name)  # Vytvorí Label pre názov zásuvky
            zapnut_button = Gtk.Button(label="Zapnúť")  # Vytvorí tlačidlo pre zapnutie
            vypnut_button = Gtk.Button(label="Vypnúť")  # Vytvorí tlačidlo pre vypnutie
            status_labels[name] = Gtk.Label()  # Vytvorí Label pre stav zásuvky
            set_led_status(name, "def")  # Nastaví predvolený stav LED
            zapnut_button.connect("clicked", lambda button, n=cislo, l=name: ovladaj_zasuvku(n, True, l))  # Pripojí funkciu pre zapnutie
            vypnut_button.connect("clicked", lambda button, n=cislo, l=name: ovladaj_zasuvku(n, False, l))  # Pripojí funkciu pre vypnutie
            zasuvky_grid.attach(label, i, 0, 1, 1)  # Pridá Label do gridu
            zasuvky_grid.attach(zapnut_button, i, 1, 1, 1)  # Pridá tlačidlo pre zapnutie do gridu
            zasuvky_grid.attach(vypnut_button, i, 2, 1, 1)  # Pridá tlačidlo pre vypnutie do gridu
            zasuvky_grid.attach(status_labels[name], i, 3, 1, 1)  # Pridá Label pre stav do gridu

        # INDISTARTER
        indistarter_c14_button = Gtk.Button(label="Spustiť INDISTARTER C14")
        indistarter_az2000_button = Gtk.Button(label="Spustiť INDISTARTER AZ2000")
        indistarter_c14_button.connect("clicked", spusti_indistarter_c14)
        indistarter_az2000_button.connect("clicked", spusti_indistarter_az2000)
        atacama_grid.attach(indistarter_c14_button, 1, 0, 1, 3)
        atacama_grid.attach(indistarter_az2000_button, 2, 0, 1, 3)

        # Strecha
        strecha_frame = Gtk.Frame()
        strecha_frame_label = Gtk.Label(label="Strecha")
        strecha_frame.set_label_widget(strecha_frame_label)
        strecha_grid = Gtk.Grid()
        strecha_grid.set_column_spacing(5)
        strecha_grid.set_row_spacing(5)
        strecha_frame.set_child(strecha_grid)
        atacama_grid.attach(strecha_frame, 3, 0, 1, 3)
        sever_button = Gtk.Button(label="Sever")
        juh_button = Gtk.Button(label="Juh")
        sever_button.connect("clicked", lambda button: ovladaj_strechu("sever"))
        juh_button.connect("clicked", lambda button: ovladaj_strechu("juh"))
        strecha_grid.attach(sever_button, 0, 0, 1, 1)
        strecha_grid.attach(juh_button, 0, 1, 1, 1)

        # WAKE-ON-LAN sekcia
        wake_frame = Gtk.Frame()
        wake_frame_label = Gtk.Label(label="WAKE-ON-LAN")
        wake_frame.set_label_widget(wake_frame_label)
        wake_grid = Gtk.Grid()
        wake_grid.set_column_spacing(5)
        wake_grid.set_row_spacing(5)
        wake_frame.set_child(wake_grid)
        grid.attach(wake_frame, 1, 0, 1, 1)

        az2000_button = Gtk.Button(label="Zapni AZ2000")
        gm3000_button = Gtk.Button(label="Zapni GM3000")
        az2000_button.connect("clicked", lambda button: wake_on_lan("00:c0:08:a9:c2:32"))
        gm3000_button.connect("clicked", lambda button: wake_on_lan(GM3000_MAC))
        wake_grid.attach(az2000_button, 0, 0, 1, 1)
        wake_grid.attach(gm3000_button, 0, 1, 1, 1)

        # OTA Aktualizácie sekcia
        ota_frame = Gtk.Frame()
        ota_frame_label = Gtk.Label(label="OTA Aktualizácie")
        ota_frame.set_label_widget(ota_frame_label)
        ota_grid = Gtk.Grid()
        ota_grid.set_column_spacing(5)
        ota_grid.set_row_spacing(5)
        ota_frame.set_child(ota_grid)
        grid.attach(ota_frame, 2, 0, 1, 1)

        aktualizovat_button = Gtk.Button(label="Aktualizovať program")
        aktualizovat_button.connect("clicked", aktualizuj_program)
        ota_grid.attach(aktualizovat_button, 0, 0, 1, 1)

        # Kamery
        kamera_atacama_label = Gtk.Label()
        kamera_atacama_label.set_markup("<a href='http://172.20.20.134'>Kamera Atacama</a>")
        kamera_atacama_label.set_use_markup(True)
        kamera_astrofoto_label = Gtk.Label()
        kamera_astrofoto_label.set_markup("<a href='http://172.20.20.131'>Kamera Astrofoto</a>")
        kamera_astrofoto_label.set_use_markup(True)
        ota_grid.attach(kamera_atacama_label, 1, 0, 1, 1)
        ota_grid.attach(kamera_astrofoto_label, 2, 0, 1, 1)

        # Konfig sekcia
        config_frame = Gtk.Frame()
        config_frame_label = Gtk.Label(label="Konfigurácia AZ2000")
        config_frame.set_label_widget(config_frame_label)
        config_grid = Gtk.Grid()
        config_grid.set_column_spacing(5)
        config_grid.set_row_spacing(5)
        config_frame.set_child(config_grid)
        grid.attach(config_frame, 3, 0, 1, 1)

        ip_label = Gtk.Label(label="IP adresa:")
        self.ip_input = Gtk.Entry()
        self.ip_input.set_text(AZ2000_IP)
        config_grid.attach(ip_label, 0, 0, 1, 1)
        config_grid.attach(self.ip_input, 0, 1, 1, 1)

        user_label = Gtk.Label(label="SSH používateľ:")
        self.user_input = Gtk.Entry()
        self.user_input.set_text(SSH_USER2)
        config_grid.attach(user_label, 1, 0, 1, 1)
        config_grid.attach(self.user_input, 1, 1, 1, 1)

        password_label = Gtk.Label(label="SSH heslo:")
        self.password_input = Gtk.Entry()
        self.password_input.set_visibility(False)
        self.password_input.set_text(SSH_PASS2)
        config_grid.attach(password_label, 2, 0, 1, 1)
        config_grid.attach(self.password_input, 2, 1, 1, 1)

        save_button = Gtk.Button(label="Uložiť nastavenia")
        save_button.connect("clicked", self.save_config)
        config_grid.attach(save_button, 3, 0, 1, 2)

        self.show()  # Zobrazí hlavné okno

    def save_config(self, button):
        """Uloží konfiguráciu AZ2000 do konfiguračného súboru."""
        global AZ2000_IP, SSH_USER2, SSH_PASS2  # Používa globálne premenné
        ip = self.ip_input.get_text()  # Získa text z IP vstupného poľa
        user = self.user_input.get_text()  # Získa text z používateľského mena
        password = self.password_input.get_text()  # Získa text z hesla
        if save_config(ip, user, password):  # Volá funkciu pre uloženie konfigurácie
            dialog = Gtk.MessageDialog(  # Vytvorí informačný dialóg
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Konfigurácia AZ2000 bola uložená.",
            )
            dialog.run()  # Spustí dialóg
            dialog.destroy()  # Zničí dialóg po zatvorení
            AZ2000_IP = ip  # Aktualizuje globálne premenné
            SSH_USER2 = user
            SSH_PASS2 = password
        else:
            dialog = Gtk.MessageDialog(  # Vytvorí chybový dialóg
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Chyba pri ukladaní konfigurácie.",
            )
            dialog.run()  # Spustí dialóg
            dialog.destroy()  # Zničí dialóg po zatvorení



def main():
    """Hlavná funkcia, volaná pri spustení programu."""
    load_config()
    app = Gtk.Application(application_id="com.example.C14Control")  # Vytvorí Gtk aplikáciu
    app.connect("activate", lambda app: MainWindow())  # Pripojí signál "activate" k vytvoreniu hlavného okna
    app.run()  # Spustí aplikáciu



if __name__ == "__main__":
    # Spustíme hlavnú funkciu
    main()
