# Licensed under the JADIV Private License v1.0 – see LICENSE file for details.
import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from wakeonlan import send_magic_packet
from datetime import datetime
import pytz
import os

ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
README_CESTA = "/home/dpv/j44softapps-socketcontrol/readme.md"
README_URL = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/readme.md"
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
        self.resize(1100, 500)  # väčšia šírka, menšia výška
        self.setMinimumSize(900, 400)  # aby sa to nedalo scvrknúť úplne

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #000000;
                font-family: Consolas, monospace;
            }
        
        QPushButton {
            background-color: #00ccff;
            color: black;
            border-radius: 8px;
            padding: 4px;
            font-size: 9pt;
            min-height: 20px;
            min-width: 45px;
        }

            }
        
            QPushButton:hover {
                background-color: #cccccc;
            }
        
            QTextEdit#logBox {
                background-color: #e0ffe0;
                color: #008000;
                font-family: Consolas;
            }
        
            QGroupBox {
                border: 2px solid #006699;
                border-radius: 10px;
                margin-top: 10px;
                padding: 8px;
            }
        
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 6px;
                color: #003366;
            }
        
            QGroupBox#wakeOnLanBox QLabel, QGroupBox#wakeOnLanBox QPushButton {
                color: #ff6600;
            }
        
            QGroupBox#indistarterBox QLabel, QGroupBox#indistarterBox QPushButton {
                color: #003366;
            }
        """)




        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)
        self.grid_layout = QtWidgets.QGridLayout(self.main_layout)

        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 1)

        self.status_labels = {}
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)
        self.grid_layout.addWidget(self.log_box, 99, 0, 1, 3)

        group_atacama = self.init_atacama_section()
        group_wol     = self.init_wake_on_lan_section()
        group_ota     = self.init_ota_section()
        group_readme  = self.init_readme_section()
        
        self.grid_layout.addWidget(group_atacama, 0, 0)
        self.grid_layout.addWidget(group_wol,     0, 1)
        self.grid_layout.addWidget(group_ota,     0, 2)
        self.grid_layout.addWidget(group_readme,  1, 2)
        self.grid_layout.addWidget(self.log_box,  2, 0, 1, 3)



        self.aktualizuj_stav_zasuviek()
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)
        self.status_timer.start(5 * 60 * 1000)

    def init_atacama_section(self):
        group_box = QtWidgets.QGroupBox("ATACAMA")
        group_box.setObjectName("indistarterBox")
        layout = QtWidgets.QGridLayout(group_box)

        zasuvky_group = QtWidgets.QGroupBox("Zásuvky")
        zasuvky_layout = QtWidgets.QGridLayout(zasuvky_group)
        for index, (name, cislo) in enumerate(ZASUVKY.items()):
            row = index // 3   # max 3 na riadok, potom nový
            col = (index % 3) * 4  # každý zásuvkový blok zaberie 4 stĺpce
        
            label = QtWidgets.QLabel(name)
            zapnut = QtWidgets.QPushButton("Zapnúť")
            vypnut = QtWidgets.QPushButton("Vypnúť")
            self.status_labels[name] = QtWidgets.QLabel()
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))
        
            zapnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
        
            zasuvky_layout.addWidget(label, row, col)
            zasuvky_layout.addWidget(zapnut, row, col + 1)
            zasuvky_layout.addWidget(vypnut, row, col + 2)
            zasuvky_layout.addWidget(self.status_labels[name], row, col + 3)

        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        ind_c14 = QtWidgets.QPushButton("Spustiť INDISTARTER C14")
        ind_az = QtWidgets.QPushButton("Spustiť INDISTARTER AZ2000")
        ind_c14.clicked.connect(self.spusti_indistarter_c14)
        ind_az.clicked.connect(self.spusti_indistarter_az2000)
        layout.addWidget(ind_c14, 1, 0, 1, 3)
        layout.addWidget(ind_az, 2, 0, 1, 3)

        strecha_group = QtWidgets.QGroupBox("Strecha")
        strecha_layout = QtWidgets.QGridLayout(strecha_group)
        self.sever_button = QtWidgets.QPushButton("Sever")
        self.juh_button = QtWidgets.QPushButton("Juh")
        self.both_button = QtWidgets.QPushButton("Both")
        self.sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))
        self.juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))
        self.both_button.clicked.connect(lambda: self.ovladaj_strechu("both"))
        strecha_layout.addWidget(self.sever_button, 0, 0)
        strecha_layout.addWidget(self.juh_button, 0, 1)
        strecha_layout.addWidget(self.both_button, 0, 2)
        layout.addWidget(strecha_group, 3, 0, 1, 3)

        cas_group = QtWidgets.QGroupBox("Načasovať strechu")
        cas_layout = QtWidgets.QGridLayout(cas_group)
        self.cas_enable = QtWidgets.QCheckBox("Aktivovať časovač")
        self.cas_enable.stateChanged.connect(self.toggle_casovac_strechy)
        self.cas_smer = QtWidgets.QComboBox()
        self.cas_smer.addItems(["sever", "juh", "both"])
        self.cas_input = QtWidgets.QLineEdit()
        self.cas_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self.cas_btn = QtWidgets.QPushButton("Nastaviť časovač")
        self.cas_btn.clicked.connect(self.nastav_casovac_strechy)
        self.cas_btn.setEnabled(False)
        cas_layout.addWidget(self.cas_enable, 0, 0, 1, 2)
        cas_layout.addWidget(QtWidgets.QLabel("Smer:"), 1, 0)
        cas_layout.addWidget(self.cas_smer, 1, 1)
        cas_layout.addWidget(QtWidgets.QLabel("Čas:"), 2, 0)
        cas_layout.addWidget(self.cas_input, 2, 1)
        cas_layout.addWidget(self.cas_btn, 3, 0, 1, 2)
        layout.addWidget(cas_group, 4, 0, 1, 3)

        self.grid_layout.addWidget(group_box, 0, 0)

        self.timer_strecha = QtCore.QTimer()
        self.timer_strecha.timeout.connect(self.skontroluj_cas_strechy)
        self.timer_strecha.start(60 * 1000)
        self.c_act = False
        self.c_smer = None
        self.c_time = None

    def init_wake_on_lan_section(self):
        box = QtWidgets.QGroupBox("WAKE-ON-LAN")
        box.setObjectName("wakeOnLanBox")
        layout = QtWidgets.QGridLayout(box)
    
        z1 = QtWidgets.QPushButton("Zapni AZ2000")
        z2 = QtWidgets.QPushButton("Zapni GM3000")
        z1.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))
        z2.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))
    
        layout.addWidget(z1, 0, 0)
        layout.addWidget(z2, 0, 1)
    
        return box


    def init_ota_section(self):
        box = QtWidgets.QGroupBox("OTA Aktualizácie")
        layout = QtWidgets.QVBoxLayout(box)
    
        but = QtWidgets.QPushButton("Aktualizovať program")
        but.clicked.connect(self.aktualizuj_program)
        layout.addWidget(but)
    
        # Odkazy na kamery
        for txt, url in [
            ("Kamera Atacama", "http://172.20.20.134"),
            ("Kamera Astrofoto", "http://172.20.20.131")
        ]:
            lbl = QtWidgets.QLabel(f"<a href='{url}'>{txt}</a>")
            lbl.setOpenExternalLinks(True)
            layout.addWidget(lbl)
    
        return box


    def init_readme_section(self):
        btn = QtWidgets.QPushButton("ℹ️ README")
        btn.setFixedWidth(100)
        btn.clicked.connect(self.zobraz_readme)
    
        box = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(box)
        layout.addWidget(btn)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignRight)
    
        return box


    def zobraz_readme(self):
        if os.path.exists(README_CESTA):
            with open(README_CESTA, "r") as f:
                text = f.read()
            dlg = QtWidgets.QMessageBox(self)
            dlg.setWindowTitle("Rozšírený popis aplikácie")
            dlg.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            dlg.setText(text[:5000] + ("..." if len(text) > 5000 else ""))
            dlg.exec_()
        else:
            self.loguj("README neexistuje.")

    def aktualizuj_program(self):
        try:
            subprocess.run(f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py -o {PROGRAM_CESTA}", shell=True, check=True)
            subprocess.run(f"curl -fsSL {README_URL} -o {README_CESTA}", shell=True, check=True)
            self.loguj("Program a README boli úspešne aktualizované.")
            QtWidgets.QMessageBox.information(self, "OTA Aktualizácia", "Program bol aktualizovaný. Reštartujem aplikáciu.")
            subprocess.Popen([sys.executable, PROGRAM_CESTA])
            sys.exit(0)
        except Exception as e:
            self.loguj(f"Chyba pri aktualizácii: {e}")

    def aktualizuj_stav_zasuviek(self):
        self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aktualizujem stav zásuviek.")
        for n, c in ZASUVKY.items():
            self.zisti_stav_zasuvky(c, n)

    def zisti_stav_zasuvky(self, cis, lab):
        try:
            out = subprocess.check_output(f"sispmctl -nqg {cis}", shell=True, text=True).strip()
            pix = "led_green.png" if out == "1" else "led_red.png" if out == "0" else "led_def.png"
            self.status_labels[lab].setPixmap(QtGui.QPixmap(pix))
        except:
            self.status_labels[lab].setPixmap(QtGui.QPixmap("led_def.png"))

    def ovladaj_zasuvku(self, cis, on, lab):
        cmd = f"sispmctl -{'o' if on else 'f'} {cis}"
        try:
            out = subprocess.check_output(cmd, shell=True)
            self.loguj(out.decode())
        except Exception as e:
            self.loguj(f"Chyba: {e}")
        self.zisti_stav_zasuvky(cis, lab)

    def spusti_indistarter_c14(self):
        try:
            out = subprocess.check_output("indistarter", shell=True)
            self.loguj(out.decode())
        except:
            self.loguj("Chyba spustenia INDISTARTER C14")

    def spusti_indistarter_az2000(self):
        try:
            out = subprocess.check_output(f"ssh {SSH_USER2}@{AZ2000_IP} indistarter", shell=True)
            self.loguj(out.decode())
        except:
            self.loguj("Chyba INDISTARTER AZ2000")

    def ovladaj_strechu(self, s):
        if s == "sever":
            p1, p2 = "crelay -s BITFT 2 ON", "crelay -s BITFT 2 OFF"
        elif s == "juh":
            p1, p2 = "crelay -s BITFT 1 ON", "crelay -s BITFT 1 OFF"
        elif s == "both":
            try:
                subprocess.run("crelay -s BITFT 1 ON", shell=True, check=True)
                subprocess.run("crelay -s BITFT 2 ON", shell=True, check=True)
                time.sleep(2)
                subprocess.run("crelay -s BITFT 1 OFF", shell=True, check=True)
                subprocess.run("crelay -s BITFT 2 OFF", shell=True, check=True)
                return
            except:
                self.loguj(f"Chyba strecha {s}")
                return
        else:
            return
        try:
            subprocess.run(p1, shell=True, check=True)
            time.sleep(2)
            subprocess.run(p2, shell=True, check=True)
        except:
            self.loguj(f"Chyba strecha {s}")

    def toggle_casovac_strechy(self, st):
        e = (st == QtCore.Qt.Checked)
        self.cas_smer.setEnabled(e)
        self.cas_input.setEnabled(e)
        self.cas_btn.setEnabled(e)
        if not e:
            self.c_act = False

    def nastav_casovac_strechy(self):
        try:
            dt = datetime.strptime(self.cas_input.text(), "%Y-%m-%d %H:%M").astimezone(pytz.utc)
            self.c_act = True
            self.c_smer = self.cas_smer.currentText()
            self.c_time = dt
        except:
            self.loguj("Chybný formát času")

    def skontroluj_cas_strechy(self):
        if self.c_act and datetime.now(pytz.utc) >= self.c_time:
            self.ovladaj_strechu(self.c_smer)
            self.c_act = False
            self.loguj("Strecha aktivovaná časovačom")

    def wake_on_lan(self, mac):
        try:
            send_magic_packet(mac)
            self.loguj(f"WOL na {mac}")
        except:
            self.loguj("Chyba WOL")

    def loguj(self, msg):
        t = QtCore.QTime.currentTime().toString()
        self.log_box.append(f"[{t}] {msg}")
        self.log_box.moveCursor(QtGui.QTextCursor.End)

class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        pix = QtGui.QPixmap("logo.png")
        super().__init__(pix)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        self.setStyleSheet("""
            QSplashScreen {
                background-color: black;
            }
            QLabel {
                color: lime;
                font-family: Consolas;
            }
            QProgressBar {
                border: 2px solid #00ff00;
                border-radius: 5px;
                background-color: #111;
            }
            QProgressBar::chunk {
                background-color: lime;
                width: 10px;
            }
        """)

        lic = QtWidgets.QLabel("Licensed under the JADIV Private License v1.0 – see LICENSE file for details.", self)
        lic.setAlignment(QtCore.Qt.AlignCenter)
        lic.setGeometry(0, pix.height(), pix.width(), 20)

        lbl = QtWidgets.QLabel("Jadiv DEVCONTROL Enterprise for Vihorlat Observatory", self)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setGeometry(0, pix.height() + 20, pix.width(), 40)

        pr = QtWidgets.QProgressBar(self)
        pr.setGeometry(10, pix.height() + 70, pix.width() - 20, 20)
        pr.setRange(0, 100)
        pr.setValue(0)
        pr.setTextVisible(False)
        self.pr = pr

        self.resize(pix.width(), pix.height() + 100)

    def simulate_loading(self):
        for i in range(101):
            self.pr.setValue(i)
            QtWidgets.qApp.processEvents()
            time.sleep(0.010)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    QtWidgets.qApp.processEvents()
    splash.simulate_loading()

    window = MainWindow()
    window.show()
    splash.finish(window)
    sys.exit(app.exec_())
