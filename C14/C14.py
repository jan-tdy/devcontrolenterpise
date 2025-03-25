import sys
import tkinter as tk
from tkinter import ttk
import subprocess
import time
import threading
import os
import socket
import webbrowser

# Konštanty
ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2,
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
CONFIG_FILE = "az2000_config.txt"

# Premenné pre konfiguráciu AZ2000
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"
SSH_PASS2 = "otj0711"
GM3000_MAC = "00:c0:08:aa:35:12"

# Funkcie
def load_config():
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
    prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
    try:
        vystup = subprocess.check_output(prikaz, shell=True)
        print(vystup.decode())
        if zapnut:
            label_name.config(bg="green")
        else:
            label_name.config(bg="red")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri ovládaní zásuvky {cislo_zasuvky}: {e}")
        label_name.config(bg="gray")

def spusti_indistarter_c14():
    try:
        c14_prikaz = "indistarter"
        c14_vystup = subprocess.check_output(c14_prikaz, shell=True)
        print(f"INDISTARTER na C14: {c14_vystup.decode()}")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní INDISTARTERA na C14: {e}")

def spusti_indistarter_az2000():
    global AZ2000_IP, SSH_USER2, SSH_PASS2
    try:
        uvex_prikaz = f"sshpass -p '{SSH_PASS2}' ssh -o StrictHostKeyChecking=no {SSH_USER2}@{AZ2000_IP} 'indistarter'"
        subprocess.run(uvex_prikaz, shell=True, check=True)
        print(f"INDISTARTER na UVEX-RPi (AZ2000) spustený.")
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní INDISTARTERA na UVEX-RPi (AZ2000): {e}")

def ovladaj_strechu(strana):
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
    print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
    try:
        mac_bytes = bytes.fromhex(mac_adresa.replace(':', ''))
        packet = b'\xff' * 6 + mac_bytes * 16
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(packet, ('<broadcast>', 9))
        print("Magic packet odoslaný.")
    except Exception as e:
        print(f"Chyba pri odosielaní magic packetu: {e}")
        messagebox.showerror("Chyba", f"Chyba pri odosielaní WOL paketu: {e}")

def aktualizuj_program():
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
        root.destroy()
    except Exception as e:
        print(f"Chyba pri aktualizácii: {e}")
        messagebox.showerror("Chyba", f"Chyba pri aktualizácii: {e}")

# wxPython verzia
import wx

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(800, 600))
        self.panel = wx.Panel(self)
        load_config()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        config_sizer = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)

        # ATACAMA sekcia
        atacama_box = wx.StaticBox(self.panel, label="ATACAMA")
        atacama_sizer = wx.StaticBoxSizer(atacama_box, wx.VERTICAL)

        zasuvky_box = wx.StaticBox(self.panel, label="Zásuvky")
        zasuvky_sizer = wx.StaticBoxSizer(zasuvky_box, wx.VERTICAL)

        self.led_labels = {}
        for name, cislo in ZASUVKY.items():
            label = wx.StaticText(self.panel, label=name)
            zapnut_button = wx.Button(self.panel, label="Zapnúť")
            vypnut_button = wx.Button(self.panel, label="Vypnúť")
            led_label = wx.StaticText(self.panel, label="")
            led_label.SetBackgroundColour("gray")
            self.led_labels[cislo] = led_label

            zapnut_button.Bind(wx.EVT_BUTTON, lambda event, c=cislo, l=led_label: self.on_zapnut_vypnut(event, c, True, l))
            vypnut_button.Bind(wx.EVT_BUTTON, lambda event, c=cislo, l=led_label: self.on_zapnut_vypnut(event, c, False, l))

            zasuvky_sizer.Add(label, 0, wx.ALL, 5)
            zasuvky_sizer.Add(zapnut_button, 0, wx.ALL, 5)
            zasuvky_sizer.Add(vypnut_button, 0, wx.ALL, 5)
            zasuvky_sizer.Add(led_label, 0, wx.ALL, 5)

        indistarter_c14_button = wx.Button(self.panel, label="Spustiť INDISTARTER C14")
        indistarter_az2000_button = wx.Button(self.panel, label="Spustiť INDISTARTER AZ2000")
        indistarter_c14_button.Bind(wx.EVT_BUTTON, self.on_spusti_indistarter_c14)
        indistarter_az2000_button.Bind(wx.EVT_BUTTON, self.on_spusti_indistarter_az2000)

        strecha_box = wx.StaticBox(self.panel, label="Strecha")
        strecha_sizer = wx.StaticBoxSizer(strecha_box, wx.VERTICAL)
        sever_button = wx.Button(self.panel, label="Sever")
        juh_button = wx.Button(self.panel, label="Juh")
        sever_button.Bind(wx.EVT_BUTTON, lambda event: self.on_ovladaj_strechu(event, "sever"))
        juh_button.Bind(wx.EVT_BUTTON, lambda event: self.on_ovladaj_strechu(event, "juh"))
        strecha_sizer.Add(sever_button, 0, wx.ALL, 5)
        strecha_sizer.Add(juh_button, 0, wx.ALL, 5)

        atacama_sizer.Add(zasuvky_sizer, 0, wx.EXPAND | wx.ALL, 10)
        atacama_sizer.Add(indistarter_c14_button, 0, wx.EXPAND | wx.ALL, 10)
        atacama_sizer.Add(indistarter_az2000_button, 0, wx.EXPAND | wx.ALL, 10)
        atacama_sizer.Add(strecha_sizer, 0, wx.EXPAND | wx.ALL, 10)
        grid_sizer.Add(atacama_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # WAKE-ON-LAN sekcia
        wake_box = wx.StaticBox(self.panel, label="WAKE-ON-LAN")
        wake_sizer = wx.StaticBoxSizer(wake_box, wx.VERTICAL)
        az2000_button = wx.Button(self.panel, label="Zapni AZ2000")
        gm3000_button = wx.Button(self.panel, label="Zapni GM3000")
        az2000_button.Bind(wx.EVT_BUTTON, lambda event: self.on_wake_on_lan(event, "00:c0:08:a9:c2:32"))
        gm3000_button.Bind(wx.EVT_BUTTON, lambda event: self.on_wake_on_lan(event, GM3000_MAC))
        wake_sizer.Add(az2000_button, 0, wx.ALL, 5)
        wake_sizer.Add(gm3000_button, 0, wx.ALL, 5)
        grid_sizer.Add(wake_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # OTA Aktualizácie sekcia
        ota_box = wx.StaticBox(self.panel, label="OTA Aktualizácie")
        ota_sizer = wx.StaticBoxSizer(ota_box, wx.VERTICAL)
        aktualizovat_button = wx.Button(self.panel, label="Aktualizovať program")
        aktualizovat_button.Bind(wx.EVT_BUTTON, self.on_aktualizuj_program)

        kamera_atacama_label = wx.StaticText(self.panel, label='Kamera Atacama', style=wx.TE_RICH2)
        kamera_atacama_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTWEIGHT_NORMAL, wx.FONTSTYLE_NORMAL))
        kamera_atacama_label.SetForegroundColour("blue")
        kamera_atacama_label.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open_new("http://172.20.20.134"))

        kamera_astrofoto_label = wx.StaticText(self.panel, label='Kamera Astrofoto', style=wx.TE_RICH2)
        kamera_astrofoto_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTWEIGHT_NORMAL, wx.FONTSTYLE_NORMAL))
        kamera_astrofoto_label.SetForegroundColour("blue")
        kamera_astrofoto_label.Bind(wx.EVT_LEFT_DOWN, lambda e: webbrowser.open_new("http://172.20.20.131"))

        ota_sizer.Add(aktualizovat_button, 0, wx.ALL, 5)
        ota_sizer.Add(kamera_atacama_label, 0, wx.ALL, 5)
        ota_sizer.Add(kamera_astrofoto_label, 0, wx.ALL, 5)
        grid_sizer.Add(ota_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # Konfig sekcia
        config_box = wx.StaticBox(self.panel, label="Konfigurácia AZ2000")
        config_sizer2 = wx.StaticBoxSizer(config_box, wx.VERTICAL)

        ip_label = wx.StaticText(self.panel, label="IP adresa:")
        self.ip_input = wx.TextCtrl(self.panel)
        self.ip_input.SetValue(AZ2000_IP)

        user_label = wx.StaticText(self.panel, label="SSH používateľ:")
        self.user_input = wx.TextCtrl(self.panel)
        self.user_input.SetValue(SSH_USER2)

        password_label = wx.StaticText(self.panel, label="SSH heslo:")
        self.password_input = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.password_input.SetValue(SSH_PASS2)

        save_button = wx.Button(self.panel, label="Uložiť nastavenia")
        save_button.Bind(wx.EVT_BUTTON, self.on_save_config)

        config_sizer2.Add(ip_label, 0, wx.ALL, 5)
        config_sizer2.Add(self.ip_input, 0, wx.EXPAND | wx.ALL, 5)
        config_sizer2.Add(user_label, 0, wx.ALL, 5)
        config_sizer2.Add(self.user_input, 0, wx.EXPAND | wx.ALL, 5)
        config_sizer2.Add(password_label, 0, wx.ALL, 5)
        config_sizer2.Add(self.password_input, 0, wx.EXPAND | wx.ALL, 5)
        config_sizer2.Add(save_button, 0, wx.EXPAND | wx.ALL, 5)
        grid_sizer.Add(config_sizer2, 1, wx.EXPAND | wx.ALL, 10)

        main_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 10)
        self.panel.SetSizer(main_sizer)
        self.Show()

    def on_zapnut_vypnut(self, event, cislo_zasuvky, zapnut, label):
        ovladaj_zasuvku(cislo_zasuvky, zapnut, label)

    def on_spusti_indistarter_c14(self, event):
        spusti_indistarter_c14()

    def on_spusti_indistarter_az2000(self, event):
        spusti_indistarter_az2000()

    def on_ovladaj_strechu(self, event, strana):
        ovladaj_strechu(strana)

    def on_wake_on_lan(self, event, mac_adresa):
        wake_on_lan(mac_adresa)

    def on_aktualizuj_program(self, event):
        aktualizuj_program()

    def on_save_config(self, event):
        global AZ2000_IP, SSH_USER2, SSH_PASS2
        ip = self.ip_input.GetValue()
        user = self.user_input.GetValue()
        password = self.password_input.GetValue()
        if save_config(ip, user, password):
            wx.MessageBox("Konfigurácia AZ2000 bola uložená.", "Info", wx.OK | wx.ICON_INFORMATION)
            AZ2000_IP = ip
            SSH_USER2 = user
            SSH_PASS2 = password
        else:
            wx.MessageBox("Chyba pri ukladaní konfigurácie.", "Chyba", wx.OK | wx.ICON_ERROR)

# PySide6 verzia
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QPushButton,
                             QLineEdit, QMessageBox, QFrame, QSizePolicy)
from PySide6.QtGui import QFont, QCursor
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - PySide6 verzia")
        self.setGeometry(100, 100, 800, 600)
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        load_config()

        grid_layout = QGridLayout()
        self.main_layout.addLayout(grid_layout)

        # ATACAMA sekcia
        atacama_frame = QFrame()
        atacama_frame.setFrameShape(QFrame.Box)
        atacama_frame.setLineWidth(1)
        atacama_layout = QVBoxLayout()

        atacama_label = QLabel("ATACAMA")
        atacama_label.setFont(QFont("Arial", 12, QFont.Bold))
        atacama_layout.addWidget(atacama_label)

        zasuvky_frame = QFrame()
        zasuvky_layout = QGridLayout()
        zasuvky_label = QLabel("Zásuvky")
        zasuvky_label.setFont(QFont("Arial", 10, QFont.Bold))
        zasuvky_layout.addWidget(zasuvky_label, 0, 0, 1, len(ZASUVKY))

        self.led_labels = {}
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QLabel(name)
            zapnut_button = QPushButton("Zapnúť")
            vypnut_button = QPushButton("Vypnúť")
            led_label = QLabel()
            led_label.setStyleSheet("background-color: gray;")
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
        indistarter_az2000_button = QPushButton("Spustiť INDISTARTER AZ2000")
        indistarter_c14_button.clicked.connect(spusti_indistarter_c14)
        indistarter_az2000_button.clicked.connect(spusti_indistarter_az2000)
        atacama_layout.addWidget(indistarter_c14_button)
        atacama_layout.addWidget(indistarter_az2000_button)

        strecha_frame = QFrame()
        strecha_layout = QHBoxLayout()
        strecha_label = QLabel("Strecha")
        strecha_label.setFont(QFont("Arial", 10, QFont.Bold))
        strecha_layout.addWidget(strecha_label)
        sever_button = QPushButton("Sever")
        juh_button = QPushButton("Juh")
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
        wake_frame.setFrameShape(QFrame.Box)
        wake_frame.setLineWidth(1)
        wake_layout = QVBoxLayout()
        wake_label = QLabel("WAKE-ON-LAN")
        wake_label.setFont(QFont("Arial", 12, QFont.Bold))
        wake_layout.addWidget(wake_label)
        az2000_button = QPushButton("Zapni AZ2000")
        gm3000_button = QPushButton("Zapni GM3000")
        az2000_button.clicked.connect(lambda: wake_on_lan("00:c0:08:a9:c2:32"))
        gm3000_button.clicked.connect(lambda: wake_on_lan(GM3000_MAC))
        wake_layout.addWidget(az2000_button)
        wake_layout.addWidget(gm3000_button)
        wake_frame.setLayout(wake_layout)
        grid_layout.addWidget(wake_frame, 0, 1)

        # OTA Aktualizácie sekcia
        ota_frame = QFrame()
        ota_frame.setFrameShape(QFrame.Box)
        ota_frame.setLineWidth(1)
        ota_layout = QVBoxLayout()
        ota_label = QLabel("OTA Aktualizácie")
        ota_label.setFont(QFont("Arial", 12, QFont.Bold))
        ota_layout.addWidget(ota_label)
        aktualizovat_button = QPushButton("Aktualizovať program")
        aktualizovat_button.clicked.connect(aktualizuj_program)
        ota_layout.addWidget(aktualizovat_button)

        kamera_atacama_label = QLabel('<a href="http://172.20.20.134">Kamera Atacama</a>')
        kamera_atacama_label.setOpenExternalLinks(True)
        kamera_atacama_label.setCursor(Qt.PointingHandCursor)
        ota_layout.addWidget(kamera_atacama_label)

        kamera_astrofoto_label = QLabel('<a href="http://172.20.20.131">Kamera Astrofoto</a>')
        kamera_astrofoto_label.setOpenExternalLinks(True)
        kamera_astrofoto_label.setCursor(Qt.PointingHandCursor)
        ota_layout.addWidget(kamera_astrofoto_label)

        ota_frame.setLayout(ota_layout)
        grid_layout.addWidget(ota_frame, 0, 2)

        # Konfig sekcia
        config_frame = QFrame()
        config_frame.setFrameShape(QFrame.Box)
        config_frame.setLineWidth(1)
        config_layout = QGridLayout()
        config_label = QLabel("Konfigurácia AZ2000")
        config_label.setFont(QFont("Arial", 12, QFont.Bold))
        config_layout.addWidget(config_label, 0, 0, 1, 3)

        ip_label = QLabel("IP adresa:")
        self.ip_input = QLineEdit(AZ2000_IP)
        user_label = QLabel("SSH používateľ:")
        self.user_input = QLineEdit(SSH_USER2)
        password_label = QLabel("SSH heslo:")
        self.password_input = QLineEdit(SSH_PASS2)
        self.password_input.setEchoMode(QLineEdit.Password)
        save_button = QPushButton("Uložiť nastavenia")
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
        global AZ2000_IP, SSH_USER2, SSH_PASS2
        ip = self.ip_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        if save_config(ip, user, password):
            QMessageBox.information(self, "Info", "Konfigurácia AZ2000 bola uložená.")
            AZ2000_IP = ip
            SSH_USER2 = user
            SSH_PASS2 = password
        else:
            QMessageBox.critical(self, "Chyba", "Chyba pri ukladaní konfigurácie.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "wx":
        app = wx.App()
        frame = MyFrame(None, "Ovládanie Hvezdárne - C14 - wxPython verzia")
        app.MainLoop()
    elif len(sys.argv) > 1 and sys.argv[1] == "qt":
        app = QApplication(sys.argv)
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
    else:
        root = tk.Tk()
        MainWindowTkinter(root)
        root.mainloop()
