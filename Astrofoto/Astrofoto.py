# Licensed under the JADIV Private License v1.0 – see LICENSE file for details.
# raspberried
import sys
import subprocess
import time
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QMessageBox
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from datetime import datetime
import pytz
import traceback
from PyQt5.QtWidgets import QInputDialog


IS_DEV = "-developer" in sys.argv
IS_FLAG1 = "-flag1" in sys.argv # add new method

ZASUVKY = {
    "KKmaly": 4,
    "ONTC": 2,
    "Parmezan": 1
}
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/C14.py"
SSH_USER = "dpv"
SSH_PASS = "otj0711"
CENTRAL2_IP = "172.20.20.133"
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"
SSH_PASS2 = "otj0711"


class Toast(QtWidgets.QLabel):
    def __init__(self, msg, typ="info", parent=None):
        super().__init__(msg, parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {'#135b13' if typ == 'success' else '#dc2525' if typ == 'error' else '#b9e9f1'};
                color: {'#155724' if typ == 'success' else '#721c24' if typ == 'error' else '#050c4d'};
                border: 2px solid black;
                border-radius: 10px;
                padding: 8px;
                font-size: 10pt;
            }}
        """)
        self.adjustSize()
        QtCore.QTimer.singleShot(3000, self.close)

    def show_(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            x = parent_geom.x() + parent_geom.width() - self.width() - 20
            y = parent_geom.y() + parent_geom.height() - self.height() - 20
            self.move(x, y)
        else:
            screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
            self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20)
        self.show()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - lite version for raspbain bullseye")
        self.main_layout = QtWidgets.QWidget()
        self.setCentralWidget(self.main_layout)

        self.main_hbox = QtWidgets.QHBoxLayout(self.main_layout)
        self.left_column = QtWidgets.QVBoxLayout()
        self.right_column = QtWidgets.QVBoxLayout()
        self.main_hbox.addLayout(self.left_column)
        self.main_hbox.addLayout(self.right_column)
    
        if IS_DEV:
            self.developer_mode_label = QtWidgets.QLabel("🛠️ DEVELOPER MODE")
            self.developer_mode_label.setStyleSheet("color: red; font-weight: bold; font-size: 15pt;")
            self.right_column.addWidget(self.developer_mode_label, alignment=QtCore.Qt.AlignRight)
    
        self.status_labels = {}
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)

    
        try:
            with open("/home/dpv/j44softapps-socketcontrol/log.txt", "r") as f:
                lines = f.readlines()
                self.log_box.setPlainText("".join(lines))
        except:
            self.log_box.setPlainText("Nepodarilo sa načítať log.")
            if IS_DEV:
                print(traceback.format_exc())
    
        self.left_column.addWidget(self.init_astrofoto_section())
        self.right_column.addWidget(self.init_wake_on_lan_section())
        self.right_column.addWidget(self.init_ota_section())
        self.right_column.addWidget(self.log_box)
    
        self.aktualizuj_stav_zasuviek()
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.aktualizuj_stav_zasuviek)
        self.status_timer.start(5 * 60 * 1000)
    
        if IS_DEV:
            self.dev_funkcie_btn = QtWidgets.QPushButton("🔧 Odomknúť úpravu funkcií")
            self.dev_funkcie_btn.clicked.connect(self.odomkni_editor_funkcii)
            self.right_column.addWidget(self.dev_funkcie_btn)
            
    def spusti_indistarter_c14(self):
        try:
            out = subprocess.check_output("indistarter", shell=True)
            self.loguj(out.decode())
        except:
            self.loguj_traceback("Chyba spustenia INDISTARTER tu")

    def spusti_indistarter_az2000(self):
        try:
            out = subprocess.check_output(f"ssh {SSH_USER2}@{AZ2000_IP} indistarter", shell=True)
            self.loguj(out.decode())
        except:
            self.loguj_traceback("Chyba INDISTARTER AZ2000")

    def init_astrofoto_section(self):
        group_box = QtWidgets.QGroupBox("astrofoto")
        layout = QtWidgets.QGridLayout(group_box)

        # Zásuvky
        zasuvky_group = QtWidgets.QGroupBox("Zásuvky")
        zasuvky_layout = QtWidgets.QGridLayout(zasuvky_group)
        for i, (name, cislo) in enumerate(ZASUVKY.items()):
            label = QtWidgets.QLabel(name)
            zapnut = QtWidgets.QPushButton("Zapnúť")
            vypnut = QtWidgets.QPushButton("Vypnúť")
            self.status_labels[name] = QtWidgets.QLabel()
            self.status_labels[name].setPixmap(QtGui.QPixmap("led_def.png"))
            zapnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, True, l))
            vypnut.clicked.connect(lambda _, n=cislo, l=name: self.ovladaj_zasuvku(n, False, l))
            zasuvky_layout.addWidget(label, i, 0)
            zasuvky_layout.addWidget(zapnut, i, 1)
            zasuvky_layout.addWidget(vypnut, i, 2)
            zasuvky_layout.addWidget(self.status_labels[name], i, 3)
        layout.addWidget(zasuvky_group, 0, 0, 1, 3)

        # INDISTARTER
        ind_c14 = QtWidgets.QPushButton("Spustiť INDISTARTER tu")
        ind_az = QtWidgets.QPushButton("null")
        ind_c14.clicked.connect(self.spusti_indistarter_c14)
        ind_az.clicked.connect(self.spusti_indistarter_az2000)
        layout.addWidget(ind_c14, 1, 0, 1, 3)
        layout.addWidget(ind_az, 2, 0, 1, 3)

        # Strecha
        strecha_group = QtWidgets.QGroupBox("Strecha")
        strecha_layout = QtWidgets.QGridLayout(strecha_group)
        self.sever_button = QtWidgets.QPushButton("Zapad")
        self.juh_button = QtWidgets.QPushButton("Vychod")
        self.both_button = QtWidgets.QPushButton("Both")
        self.sever_button.clicked.connect(lambda: self.ovladaj_strechu("sever"))
        self.juh_button.clicked.connect(lambda: self.ovladaj_strechu("juh"))
        self.both_button.clicked.connect(lambda: self.ovladaj_strechu("both"))
        strecha_layout.addWidget(self.sever_button, 0, 0)
        strecha_layout.addWidget(self.juh_button, 0, 1)
        strecha_layout.addWidget(self.both_button, 0, 2)
        layout.addWidget(strecha_group, 3, 0, 1, 3)

        # Časovač strechy
        cas_group = QtWidgets.QGroupBox("Načasovať strechu")
        cas_layout = QtWidgets.QGridLayout(cas_group)
        self.cas_enable = QtWidgets.QCheckBox("Aktivovať časovač")
        self.cas_enable.stateChanged.connect(self.toggle_casovac_strechy)
        self.cas_smer = QtWidgets.QComboBox()
        self.cas_smer.addItems(["sever", "juh", "both"])
        self.cas_datetime = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.cas_datetime.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.cas_datetime.setCalendarPopup(True)
        self.cas_btn = QtWidgets.QPushButton("Nastaviť časovač")
        self.cas_btn.clicked.connect(self.nastav_casovac_strechy)
        self.cas_btn.setEnabled(False)
        cas_layout.addWidget(self.cas_enable, 0, 0, 1, 2)
        cas_layout.addWidget(QtWidgets.QLabel("Smer:"), 1, 0)
        cas_layout.addWidget(self.cas_smer, 1, 1)
        cas_layout.addWidget(QtWidgets.QLabel("Dátum a čas:"), 2, 0)
        cas_layout.addWidget(self.cas_datetime, 2, 1)
        cas_layout.addWidget(self.cas_btn, 3, 0, 1, 2)
        layout.addWidget(cas_group, 4, 0, 1, 3)

        # Timer strechy
        self.timer_strecha = QtCore.QTimer()
        self.timer_strecha.timeout.connect(self.skontroluj_cas_strechy)
        self.timer_strecha.start(60 * 1000)
        self.c_act = False
        self.c_smer = None
        self.c_time = None

        return group_box

    def init_wake_on_lan_section(self):
        box = QtWidgets.QGroupBox("WAKE-ON-LAN")
        lay = QtWidgets.QGridLayout(box)
        z1 = QtWidgets.QPushButton("null")
        z2 = QtWidgets.QPushButton("null")
        z1.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))
        z2.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))
        lay.addWidget(z1, 0, 0)
        lay.addWidget(z2, 0, 1)
        return box

    def init_ota_section(self):
        box = QtWidgets.QGroupBox("OTA Aktualizácie")
        lay = QtWidgets.QGridLayout(box)

        but = QtWidgets.QPushButton("🔄 Aktualizovať program")
        but.clicked.connect(self.aktualizuj_program)
        lay.addWidget(but, 0, 0, 1, 2)

        return box


    def loguj_traceback(self, msg, typ="error"):
        tb = traceback.format_exc()
        self.loguj(f"{msg}\n{tb}" if IS_DEV else msg, typ=typ)

    def aktualizuj_stav_zasuviek(self):
        self.loguj(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aktualizujem stav zásuviek.")
        for n, c in ZASUVKY.items():
            self.zisti_stav_zasuvky(c, n)
    def ovladaj_zasuvku(self, cis, on, lab):
        cmd = f"sispmctl -{'o' if on else 'f'} {cis}"
        try:
            out = subprocess.check_output(cmd, shell=True)
            self.loguj(out.decode())
        except Exception as e:
            self.loguj(f"Chyba: {e}")
        self.zisti_stav_zasuvky(cis, lab)
        
    def zisti_stav_zasuvky(self, cis, lab):
        try:
            out = subprocess.check_output(f"sispmctl -nqg {cis}", shell=True, text=True).strip()
            pix = (
                "led_green.png" if out == "1" else
                "led_red.png" if out == "0" else
                "led_def.png"
            )
            self.status_labels[lab].setPixmap(QtGui.QPixmap(pix))
        except:
            self.loguj_traceback(f"Chyba zisťovania stavu zásuvky {lab}")
            self.status_labels[lab].setPixmap(QtGui.QPixmap("led_def.png"))

    def ovladaj_strechu(self, s):
        PRIKAZY_STRECHA = {
            "sever": [
                "pyhid-usb-relay on 1",
                "sleep 2",
                "pyhid-usb-relay off 1",
            ],
            "juh": [
                "pyhid-usb-relay on 2",
                "sleep 2",
                "pyhid-usb-relay off 2",
            ],
            "both": [
                "pyhid-usb-relay on 1",
                "sleep 1",
                "pyhid-usb-relay on 2",
                "sleep 2",
                "pyhid-usb-relay off 1",
                "sleep 1",
                "pyhid-usb-relay off 2",
            ]
        }
    
        prikazy = PRIKAZY_STRECHA.get(s)
        if not prikazy:
            self.loguj(f"Neznámy smer strechy: {s}", typ="error")
            return
    
        try:
            for cmd in prikazy:
                subprocess.run(cmd, shell=True, check=True)
            self.loguj(f"Strecha ovládaná ({s})", typ="success")
        except Exception as e:
            self.loguj(f"Chyba pri ovládaní strechy ({s}): {e}", typ="error")


    def toggle_casovac_strechy(self, st):
        e = (st == QtCore.Qt.Checked)
        self.cas_smer.setEnabled(e)
        self.cas_datetime.setEnabled(e)
        self.cas_btn.setEnabled(e)
        if not e:
            self.c_act = False
            
    def nastav_casovac_strechy(self):
        try:
            qdt = self.cas_datetime.dateTime()
            self.c_time = qdt.toPyDateTime().replace(tzinfo=pytz.utc)

            self.c_act = True
            self.c_smer = self.cas_smer.currentText()
            self.loguj(f"Časovač nastavený na UTC {self.c_time} pre smer {self.c_smer}", typ="success")
        except:
            self.loguj_traceback("Chyba pri nastavovaní časovača")



    def skontroluj_cas_strechy(self):
        if self.c_act and datetime.now(pytz.utc) >= self.c_time:
            self.ovladaj_strechu(self.c_smer)
            self.c_act = False
            self.loguj("Strecha aktivovaná časovačom", typ="success")

    def wake_on_lan(self, mac):
        try:
            # Check if the `wakeonlan` command is available
            subprocess.run(["which", "wakeonlan"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # If the command is found, proceed with sending the magic packet
            from wakeonlan import send_magic_packet
            send_magic_packet(mac)
            self.loguj(f"WOL na {mac} nieje podporovany", typ="warning")
        
        except subprocess.CalledProcessError:
            # If `wakeonlan` command is not found, show a dialog box to notify the user
            self.show_wol_not_supported_dialog()
        except Exception as e:
            self.loguj_traceback("Chyba WOL")

    def show_wol_not_supported_dialog(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("WOL not supported")
        msg.setText("Wake on LAN is not supported on this OS.")
        QtWidgets.QMessageBox.critical(self, "WOL not supported","Wake on LAN is not supported on this OS.")


    def spusti_stream(self, rtsp_url):
        try:
            subprocess.Popen(["ffplay", "-fflags", "nobuffer", "-i", rtsp_url])
            self.loguj(f"Spustený RTSP stream: {rtsp_url}", typ="success")
        except Exception:
            self.loguj_traceback(f"Chyba pri spúšťaní streamu {rtsp_url}")

    def aktualizuj_program(self):
        try:
            curl_cmd = (
                f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py"
                f" -o {PROGRAM_CESTA}"
            )
            subprocess.run(curl_cmd, shell=True, check=True)
            self.loguj("Program bol úspešne aktualizovaný.")
            QtWidgets.QMessageBox.information(self, "OTA Aktualizácia", "Program bol aktualizovaný. Reštartujem aplikáciu po zavretí tohto dialógu, ak nebude úspech naštartujte aplikáciu manuálne.", typ="success")
            subprocess.Popen([sys.executable, PROGRAM_CESTA])
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            self.loguj_traceback(f"Chyba pri aktualizácii programu: {e}")
        except Exception:
            self.loguj_traceback("Neočakávaná chyba pri aktualizácii")
            
    def odomkni_editor_funkcii(self):
        pin, ok = QtWidgets.QInputDialog.getText(self, "Developer PIN", "Zadaj PIN pre úpravu funkcií:", QtWidgets.QLineEdit.Password)
        if ok and pin == "6589":
            editor = QtWidgets.QDialog(self)
            editor.setWindowTitle("Live úprava funkcií")
            editor.resize(800, 500)
            layout = QtWidgets.QVBoxLayout(editor)

            info = QtWidgets.QLabel("Tu môžeš upraviť funkcie `ovladaj_strechu`, `ovladaj_zasuvku` a `aktualizuj_program`.\nZmeny sa prejavia po reštarte.")
            layout.addWidget(info)

            try:
                with open(PROGRAM_CESTA, "r") as f:
                    obsah = f.read()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Chyba", f"Nepodarilo sa načítať súbor:\n{e}")
                return

            self.editor_area = QtWidgets.QPlainTextEdit()
            self.editor_area.setPlainText(obsah)
            layout.addWidget(self.editor_area)

            btn_save = QtWidgets.QPushButton("💾 Uložiť zmeny")
            btn_save.clicked.connect(self.uloz_zmeny_do_programu)
            layout.addWidget(btn_save)

            editor.exec_()
        else:
            self.loguj("Zlý PIN alebo zrušené", typ="error")

    def uloz_zmeny_do_programu(self):
        try:
            with open(PROGRAM_CESTA, "w") as f:
                f.write(self.editor_area.toPlainText())
            QtWidgets.QMessageBox.information(
                self, "Hotovo", "Zmeny boli uložené. Program sa teraz reštartuje."
            )
            subprocess.Popen([sys.executable, PROGRAM_CESTA, "-developer"])
            sys.exit(0)
        except:
            self.loguj_traceback("Nepodarilo sa uložiť úpravy")

    def loguj(self, msg, typ="info"):
        t = QtCore.QTime.currentTime().toString()
        self.log_box.append(f"[{t}] {msg}")
        self.log_box.moveCursor(QtGui.QTextCursor.End)
        try:
            with open("/home/dpv/j44softapps-socketcontrol/log.txt", "a") as f:
                f.write(f"[{t}] {msg}\n")
        except Exception as e:
            if IS_DEV:
                print("Chyba pri ukladaní logu:", traceback.format_exc())
            else:
                print("Chyba pri ukladaní logu:", e)
        toast = Toast(msg, typ=typ, parent=self)
        toast.show_()

class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        super().__init__()
        self.resize(1000, 750)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: white;")

        # === LOGO ===
        logo = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("logo.png")
        scaled = pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        logo.setPixmap(scaled)
        logo.setFixedSize(scaled.size())
        logo.move((self.width() - scaled.width()) // 2, 10)

        base_y = 120  # všetky texty začínajú až pod logom

        # === Nadpis ===
        lbl = QtWidgets.QLabel("🛰️ Jadiv DEVCONTROL raspberried Enterprise for Vihorlat Observatory", self)
        lbl.setStyleSheet("color: #224488; font-weight: bold; font-size: 14pt;")
        lbl.adjustSize()
        lbl.move((self.width() - lbl.width()) // 2, base_y)

        # === Verzia ===
        verzia = QtWidgets.QLabel("Lite version -- raspberried-bullseye", self)
        verzia.setStyleSheet("color: #666; font-size: 10pt;")
        verzia.adjustSize()
        verzia.move((self.width() - verzia.width()) // 2, base_y + 30)

        # === Popis ===
        extra = QtWidgets.QLabel("Loading the program, that may take a few moments.\nInicializujem všetko potrebné.\nKód obsahuje vyše 1000 riadkov...", self)
        extra.setStyleSheet("color: #000000; font-size: 9pt;")
        extra.setAlignment(QtCore.Qt.AlignCenter)
        extra.adjustSize()
        extra.move((self.width() - extra.width()) // 2, base_y + 60)

        # === Licencia ===
        lic = QtWidgets.QLabel("Licensed under the JADIV Private License v1.0 – see LICENSE file for details.", self)
        lic.setStyleSheet("color: blue; font-size: 10px;")
        lic.adjustSize()
        lic.move((self.width() - lic.width()) // 2, base_y + 120)

        # === Progress bar ===
        pr = QtWidgets.QProgressBar(self)
        pr.setGeometry(250, base_y + 150, 500, 20)
        pr.setRange(0, 100)
        pr.setValue(0)
        pr.setTextVisible(False)
        self.pr = pr

    def simulate_loading(self):
        base_y = 120  # 
        spravy = [
            "🔧 Aktivujem sekciu spusti_indistarter_c14()...",
            "📡 Aktivujem sekciu spusti_wakeonlan_c14()...",
            "🔌 Aktivujem sekciu init_relay_connection()...",
            "📁 Aktivujem sekciu init_program_paths()...",
            "📦 Aktivujem sekciu init_astrofoto_section()...",
            "🧪 Aktivujem sekciu kontrola_relé_stavu()...",
            "📋 Aktivujem sekciu init_logging_system()...",
            "🔐 Aktivujem sekciu overenie_hesiel()...",
            "📡 Aktivujem sekciu init_remote_connect()...",
            "🕒 Aktivujem sekciu casovac_strechy()...",
            "🗄️ Aktivujem sekciu nacitanie_logu()...",
            "🧰 Aktivujem sekciu init_debug_modul()...",
            "🧠 Aktivujem sekciu init_gui_components()...",
            "🔧 Aktivujem sekciu init_zasuvky_module()...",
            "🔁 Aktivujem sekciu prepni_strechu_juh()...",
            "🌐 Aktivujem sekciu connect_to_az2000()...",
            "🔎 Aktivujem sekciu kontrola_usb_pripojeni()...",
            "📑 Aktivujem sekciu nacitaj_konfiguraciu()...",
            "📊 Aktivujem sekciu zobraz_graf_teploty()...",
            "🚀 Dokončujem inicializáciu hlavného rozhrania..."
        ]

        # Použijeme len jeden QLabel pre status hlášky
        self.status_label = QtWidgets.QLabel("", self)
        self.status_label.setStyleSheet("color: #444; font-size: 10pt;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setGeometry(0, base_y + 100, self.width(), 20)

        celkovy_cas = 5.0  # celé načítavanie trvá 5 sekúnd
        krok_cas = celkovy_cas / len(spravy)

        for i, sprava in enumerate(spravy):
            self.status_label.setText(sprava)
            self.pr.setValue(int((i + 1) * 100 / len(spravy)))
            QtWidgets.qApp.processEvents()
            time.sleep(krok_cas)


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
    bug_window = QtWidgets.QWidget()
    bug_window.setWindowTitle("SPLASH BUG – Chyba pri štarte hlavného okna")
    bug_window.setMinimumSize(500, 200)
    layout = QtWidgets.QVBoxLayout(bug_window)

    error_label = QtWidgets.QLabel(
        "Nastal problém pri štarte hlavného okna aplikácie.\n"
        "Pravdepodobne je chyba v aktualizovanom kóde.\n"
        "Ak nieste vývojár kódu obráťťe sa na JaPySoft.\n"
    )
    error_label.setStyleSheet("color: red; font-size: 11pt; font-weight: bold;")
    layout.addWidget(error_label)

    error_details = QtWidgets.QTextEdit()
    error_details.setReadOnly(True)
    error_details.setPlainText(str(e))
    layout.addWidget(error_details)

    def spusti_update():
        try:
            subprocess.run(
                f"curl -fsSL https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py -o {PROGRAM_CESTA}",
                shell=True, check=True
            )
            QtWidgets.QMessageBox.information(bug_window, "Hotovo", "Program bol aktualizovaný. Spusť ho znova.")
            bug_window.close()
        except Exception as ex:
            QtWidgets.QMessageBox.critical(bug_window, "Chyba", f"Zlyhala aktualizácia: {ex}")

    def nainstaluj_zavislosti():
        try:
            subprocess.run("pip install pyqt5 wakeonlan pytz opencv-python", shell=True)
            QtWidgets.QMessageBox.information(bug_window, "OK", "Závislosti boli nainštalované.")
        except Exception as ex:
            QtWidgets.QMessageBox.critical(bug_window, "Chyba", f"Zlyhala inštalácia závislostí: {ex}")

    btn_update = QtWidgets.QPushButton("Aktualizovať program")
    btn_update.clicked.connect(spusti_update)
    layout.addWidget(btn_update)

    btn_install = QtWidgets.QPushButton("Nainštalovať závislosti")
    btn_install.clicked.connect(nainstaluj_zavislosti)
    layout.addWidget(btn_install)

    bug_window.show()

sys.exit(app.exec_())
