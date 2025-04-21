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
SSH_USER = "dpv"
SSH_PASS = "otj0711"
CENTRAL2_IP = "172.20.20.133"
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"
SSH_PASS2 = "otj0711"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14")
        self.resize(1280, 720)
        self.setMinimumSize(1024, 600)


        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #212121;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 9.5pt;
            }
        
            QPushButton {
                background-color: #d4e157;
                color: #212121;
                border: none;
                border-radius: 10px;
                padding: 6px 14px;
                font-weight: 600;
            }
        
            QPushButton:hover {
                background-color: #c0ca33;
            }
        
            QPushButton:pressed {
                background-color: #afb42b;
            }
        
            QTextEdit#logBox {
                background-color: #f9fbe7;
                color: #33691e;
                border: 1px solid #cddc39;
                border-radius: 10px;
                padding: 8px;
                font-size: 9pt;
            }
        
            QGroupBox {
                background-color: #f1f8e9;
                border: 2px solid #cddc39;
                border-radius: 14px;
                padding: 12px;
                margin-top: 8px;
            }
        
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 9.5pt;
                color: #558b2f;
            }
        
            QLabel {
                color: #212121;
                font-weight: 500;
                font-size: 9.5pt;
            }
        
            QLineEdit, QComboBox, QTextEdit, QCheckBox {
                background-color: #ffffff;
                border: 1px solid #cddc39;
                border-radius: 8px;
                padding: 6px;
                font-size: 9pt;
            }
        
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #aeea00;
            }
        
            QCheckBox {
                spacing: 6px;
            }
        
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #f1f8e9;
                border-radius: 5px;
                width: 8px;
            }
        
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #cddc39;
                border-radius: 5px;
            }
        
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #afb42b;
            }
        
            QToolTip {
                background-color: #d4e157;
                color: black;
                border: 1px solid #cddc39;
                padding: 6px;
                border-radius: 5px;
                font-size: 9pt;
            }
        """)



        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        
        content_widget = QtWidgets.QWidget()
        scroll.setWidget(content_widget)
        
        self.main_layout = QtWidgets.QVBoxLayout(content_widget)


        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)

        self.status_labels = {}
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)
        self.grid_layout.addWidget(self.log_box, 3, 0, 1, 2)

        # Sem to patrí:
        self.log_file_path = "/home/dpv/j44softapps-socketcontrol/log.txt"
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, "r") as f:
                self.log_box.setPlainText(f.read())
        
        group_atacama = self.init_atacama_section()
        group_wol     = self.init_wake_on_lan_section()
        group_ota     = self.init_ota_section()
        group_kamery = self.init_kamery_section()
        
        self.grid_layout.addWidget(group_atacama, 0, 0)
        self.grid_layout.addWidget(group_ota, 0, 1)
        self.grid_layout.addWidget(self.group_strecha, 1, 0)
        self.grid_layout.addWidget(group_kamery, 1, 1)
        self.grid_layout.addWidget(group_wol, 2, 1)
        self.grid_layout.addWidget(self.log_box, 3, 0, 1, 2)  # cez celú šírku

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
            label = QtWidgets.QLabel(name)
            zapnut = QtWidgets.QPushButton("Zapnúť")
            vypnut = QtWidgets.QPushButton("Vypnúť")
            self.status_labels[name] = QtWidgets.QLabel()
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))
        
            zapnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
        
            zasuvky_layout.addWidget(label, index, 0)
            zasuvky_layout.addWidget(zapnut, index, 1)
            zasuvky_layout.addWidget(vypnut, index, 2)
            zasuvky_layout.addWidget(self.status_labels[name], index, 3)  # ← TU presunuté


        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        ind_c14 = QtWidgets.QPushButton("Spustiť INDISTARTER C14")
        ind_az = QtWidgets.QPushButton("Spustiť INDISTARTER AZ2000")
        ind_c14.clicked.connect(self.spusti_indistarter_c14)
        ind_az.clicked.connect(self.spusti_indistarter_az2000)
        layout.addWidget(ind_c14, 1, 0, 1, 3)
        layout.addWidget(ind_az, 2, 0, 1, 3)

        self.group_strecha = QtWidgets.QGroupBox("Strecha")
        strecha_layout = QtWidgets.QGridLayout(self.group_strecha)
        self.sever_button = QtWidgets.QPushButton("Sever")
        self.juh_button = QtWidgets.QPushButton("Juh")
        self.both_button = QtWidgets.QPushButton("Both")
        self.sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))
        self.juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))
        self.both_button.clicked.connect(lambda: self.ovladaj_strechu("both"))
        strecha_layout.addWidget(self.sever_button, 0, 0)
        strecha_layout.addWidget(self.juh_button, 0, 1)
        strecha_layout.addWidget(self.both_button, 0, 2)
        layout.addWidget(self.group_strecha, 3, 0, 1, 3)

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
        box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
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
        box.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        layout = QtWidgets.QVBoxLayout(box)
    
        but = QtWidgets.QPushButton("Aktualizovať program")
        but.clicked.connect(self.aktualizuj_program)
        layout.addWidget(but)
    
        return box



    def init_kamery_section(self):
        box = QtWidgets.QGroupBox("Kamery")
        box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        layout = QtWidgets.QVBoxLayout(box)
    
        for txt, url in [
            ("Kamera Atacama", "http://172.20.20.134"),
            ("Kamera Astrofoto", "http://172.20.20.131")
        ]:
            lbl = QtWidgets.QLabel(f"<a href='{url}'>{txt}</a>")
            lbl.setOpenExternalLinks(True)
            layout.addWidget(lbl)
    
        return box

    def aktualizuj_program(self):
        try:
            subprocess.run(f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py -o {PROGRAM_CESTA}", shell=True, check=True)
            subprocess.run(f"curl -fsSL {README_URL} -o {README_CESTA}", shell=True, check=True)
            self.loguj("Program a README boli úspešne aktualizované. Reštarujem program", "success")
            subprocess.Popen([sys.executable, PROGRAM_CESTA])
            sys.exit(0)
        except Exception as e:
            self.loguj("Chyba pri aktualizácii! {e}", "error")

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

    def loguj(self, msg, typ="info"):
        if "Aktualizujem stav zásuviek" in msg:
            return  # nechceme ukladať tieto správy
    
        t = QtCore.QTime.currentTime().toString()
        full_msg = f"[{t}] {msg}"
    
        self.log_box.append(full_msg)
        self.log_box.moveCursor(QtGui.QTextCursor.End)
        self.zobraz_toast(msg, typ)
    
        try:
            with open(self.log_file_path, "a") as f:
                f.write(full_msg + "\n")
        except Exception as e:
            print("Chyba pri ukladaní logu:", e)


    def zobraz_toast(self, text, typ="info", trvanie_ms=3000):
        toast = QtWidgets.QLabel(self)
        
        farby = {
            "info": "#007bff",     # modrá
            "success": "#28a745",  # zelená
            "error": "#dc3545"     # červená
        }
        ikony = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌"
        }
    
        farba = farby.get(typ, "#333")
        ikona = ikony.get(typ, "🔔")
    
        toast.setText(f"{ikona} {text}")
    
        # 🌟 Tieňový efekt
        effect = QtWidgets.QGraphicsDropShadowEffect()
        effect.setBlurRadius(15)
        effect.setOffset(4, 4)
        effect.setColor(QtGui.QColor(0, 0, 0, 160))  # jemný tieň
        toast.setGraphicsEffect(effect)
    
        toast.setStyleSheet(f"""
            background-color: {farba};
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 10pt;
        """)
        toast.setWindowFlags(QtCore.Qt.ToolTip)
        toast.adjustSize()
        toast.move(self.width() - toast.width() - 20, self.height() - toast.height() - 60)
        toast.show()
    
        QtCore.QTimer.singleShot(trvanie_ms, toast.close)

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

    try:
        window = MainWindow()
        window.show()
        splash.finish(window)
    except Exception as e:
        splash.close()

        # Náhradné okno pri chybe
        bug_window = QtWidgets.QWidget()
        bug_window.setWindowTitle("SPLASH BUG – Chyba pri štarte hlavného okna")
        bug_window.setMinimumSize(500, 200)
        layout = QtWidgets.QVBoxLayout(bug_window)

        error_label = QtWidgets.QLabel("Nastal problém pri štarte hlavného okna aplikácie.\nPravdepodobne je chyba v aktualizovanom kóde.\n")
        error_label.setStyleSheet("color: red; font-size: 11pt; font-weight: bold;")
        layout.addWidget(error_label)

        # Výpis chyby
        error_details = QtWidgets.QTextEdit()
        error_details.setReadOnly(True)
        error_details.setPlainText(str(e))
        layout.addWidget(error_details)

        # Tlačidlo na aktualizáciu programu
        def spusti_update():
            try:
                subprocess.run(
                    f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py -o {PROGRAM_CESTA}",
                    shell=True, check=True)
                QtWidgets.QMessageBox.information(bug_window, "Hotovo", "Program bol aktualizovaný. Spusť ho znova.")
                bug_window.close()
            except Exception as ex:
                QtWidgets.QMessageBox.critical(bug_window, "Chyba", f"Zlyhala aktualizácia: {ex}")

        btn_update = QtWidgets.QPushButton("Aktualizovať program")
        btn_update.clicked.connect(spusti_update)
        layout.addWidget(btn_update)

        bug_window.show()

    sys.exit(app.exec_())
