import sys
import subprocess
import time
import gi
import threading
import os

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

# Konštanty
ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2,
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
CONFIG_FILE = "az2000_config.txt"  # Konfiguračný súbor
UPDATE_SCRIPT = "update_c14.sh"  # Skript pre aktualizáciu
SEND_MAGIC_PACKET_SCRIPT = "/home/dpv/send_magic_packet.sh" # Skript pre odosielanie magic packetov

# Premenné pre konfiguráciu AZ2000 (predvolené hodnoty)
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"
SSH_PASS2 = "otj0711"
GM3000_MAC = "00:c0:08:aa:35:12" # MAC adresa pre GM3000

def load_config():
    """Načíta konfiguráciu AZ2000 z konfiguračného súboru."""
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
        # Vytvor prázdny konfiguračný súbor, aby sa predišlo opakovaným chybám pri ďalších pokusoch o načítanie
        try:
            with open(CONFIG_FILE, "w") as f:
                pass
        except Exception as e:
            print(f"Chyba pri vytváraní prázdneho konfiguračného súboru: {e}")
    except Exception as e:
        print(f"Chyba pri načítaní konfigurácie: {e}")



def save_config(ip, user, password):
    """Uloží konfiguráciu AZ2000 do konfiguračného súboru."""
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



def ovladaj_zasuvku(cislo_zasuvky, zapnut, label_name):
    """Ovláda zadanú zásuvku pomocou príkazu `sispmctl`."""
    prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
    try:
        vystup = subprocess.check_output(prikaz, shell=True)
        print(vystup.decode())
        GLib.idle_add(set_led_status, label_name, "green" if zapnut else "red")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
        GLib.idle_add(set_led_status, label_name, "def")



def spusti_indistarter_c14():
    """Spustí príkaz `indistarter` na C14."""
    try:
        c14_prikaz = "indistarter"
        c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
        print(f"INDISTARTER na C14: {c14_vystup.decode()}")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")



def spusti_indistarter_az2000():
    """Spustí príkaz `indistarter` na UVEX-RPi (AZ2000) cez SSH."""
    global AZ2000_IP, SSH_USER2, SSH_PASS2
    try:
        uvex_prikaz = f"sshpass -p '{SSH_PASS2}' ssh -o StrictHostKeyChecking=no {SSH_USER2}@{AZ2000_IP} 'indistarter'"
        subprocess.run(uvex_prikaz, shell=True, check=True)
        print(f"INDISTARTER na UVEX-RPi (AZ2000) spustený.")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")



def ovladaj_strechu(strana):
    """Ovláda strechu (sever/juh) pomocou príkazu `crelay`."""
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
    """Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN."""
    print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
    try:
        subprocess.run([SEND_MAGIC_PACKET_SCRIPT, mac_adresa], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri odosielaní magic packetu: {e}")
        show_error_dialog(f"Chyba pri odosielaní WOL paketu: {e}")


def aktualizuj_program():
    """Aktualizuje program z GitHub repozitára pomocou skriptu."""
    try:
        # Spustíme skript na aktualizáciu v samostatnom procese
        subprocess.Popen([UPDATE_SCRIPT], close_fds=True)
        print("Aktualizácia programu prebieha na pozadí. Aplikácia bude reštartovaná po dokončení.")
        # Ukončíme aplikáciu GTK, skript ju reštartuje
        GLib.idle_add(Gtk.main_quit)
    except Exception as e:
        print(f"Chyba pri spúšťaní aktualizačného skriptu: {e}")
        show_error_dialog(f"Chyba pri aktualizácii: {e}")


def set_led_status(label_name, farba):
    """Nastaví farbu LEDky v GUI pomocou CSS štýlov."""
    label = status_labels[label_name]
    if farba == "green":
        label.set_markup('<span foreground="green">●</span>')
    elif farba == "red":
        label.set_markup('<span foreground="red">●</span>')
    else:
        label.set_markup('<span foreground="gray">●</span>')  # Alebo inú predvolenú farbu


def show_error_dialog(message):
    """Zobrazí chybový dialóg."""
    dialog = Gtk.MessageDialog(
        parent=None,  # Parent okno môže byť None, ak nemáme hlavné okno
        flags=Gtk.DialogFlags.MODAL,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=message,
    )
    dialog.run()
    dialog.destroy()



class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ovládanie Hvezdárne - C14 - GTK 4 verzia")
        self.set_default_size(800, 600)
        self.margin_start = 10
        self.margin_end = 10
        self.margin_top = 10
        self.margin_bottom = 10

        load_config()

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        self.set_child(grid)

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

        global status_labels
        status_labels = {}
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = Gtk.Label(label=name)
            zapnut_button = Gtk.Button(label="Zapnúť")
            vypnut_button = Gtk.Button(label="Vypnúť")
            status_labels[name] = Gtk.Label()
            set_led_status(name, "def")
            zapnut_button.connect("clicked", lambda button, n=cislo, l=name: ovladaj_zasuvku(n, True, l))
            vypnut_button.connect("clicked", lambda button, n=cislo, l=name: ovladaj_zasuvku(n, False, l))
            zasuvky_grid.attach(label, i, 0, 1, 1)
            zasuvky_grid.attach(zapnut_button, i, 1, 1, 1)
            zasuvky_grid.attach(vypnut_button, i, 2, 1, 1)
            zasuvky_grid.attach(status_labels[name], i, 3, 1, 1)

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

        self.show()

    def save_config(self, button):
        """Uloží konfiguráciu AZ2000 do konfiguračného súboru."""
        global AZ2000_IP, SSH_USER2, SSH_PASS2
        ip = self.ip_input.get_text()
        user = self.user_input.get_text()
        password = self.password_input.get_text()
        if save_config(ip, user, password):
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Konfigurácia AZ2000 bola uložená.",
            )
            dialog.run()
            dialog.destroy()
            AZ2000_IP = ip
            SSH_USER2 = user
            SSH_PASS2 = password
        else:
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Chyba pri ukladaní konfigurácie.",
            )
            dialog.run()
            dialog.destroy()



def main():
    """Hlavná funkcia, volaná pri spustení programu."""
    load_config()
    app = Gtk.Application(application_id="com.example.C14Control")
    app.connect("activate", lambda app: MainWindow())
    app.run()



if __name__ == "__main__":
    # Spustíme hlavnú funkciu
    main()
