# Licensed under the MIT License – see LICENSE file for details.
# ubunted
import sys
import subprocess
import time
from pathlib import Path
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QMessageBox
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from datetime import datetime
import pytz
import traceback
import cv2
from PyQt5.QtWidgets import QInputDialog


IS_DEV = "-developer" in sys.argv
IS_FLAG1 = "-flag1" in sys.argv

ZASUVKY = {
    "NOUT": 4,
    "C14": 3,
    "RC16": 2
}
SSH_USER = "dpv"
SSH_PASS = "otj0711"  # WARNING: credential in source — not for public release
CENTRAL2_IP = "172.20.20.133"
AZ2000_IP = "172.20.20.116"
SSH_USER2 = "pi2"
SSH_PASS2 = "otj0711"  # WARNING: credential in source — not for public release
# TODO: update after repo move
GITHUB_RAW_URL = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py"


class Toast(QtWidgets.QLabel):
    def __init__(self, msg, typ="info", parent=None):
        super().__init__(msg, parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
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


class RtspWorker(QtCore.QThread):
    """Streams an RTSP feed in background; emits pixmaps via signal (main-thread safe)."""
    frame_ready = QtCore.pyqtSignal(QtGui.QPixmap)
    error_signal = QtCore.pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self._url = url
        self._running = False

    def run(self):
        cap = cv2.VideoCapture(self._url)
        if not cap.isOpened():
            self.error_signal.emit(f"Cannot open RTSP stream: {self._url}")
            return
        self._running = True
        while self._running:
            ret, frame = cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(qimg).scaled(320, 240, QtCore.Qt.KeepAspectRatio)
            self.frame_ready.emit(pix)
            self.msleep(50)
        cap.release()

    def stop(self):
        self._running = False
        self.wait()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._toasts: list = []
        self.setWindowTitle("Ovládanie Hvezdárne - C14 - lite version for ubuntu 24.04")
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

        self.kamera_label_atacama = QtWidgets.QLabel()
        self.kamera_label_astro = QtWidgets.QLabel()
        self.rtsp_worker_atacama = None
        self.rtsp_worker_astro = None

        try:
            with open("/home/dpv/j44softapps-socketcontrol/log.txt", "r") as f:
                lines = f.readlines()
                self.log_box.setPlainText("".join(lines[-100:]))
        except Exception:
            self.log_box.setPlainText("Nepodarilo sa načítať log.")
            if IS_DEV:
                print(traceback.format_exc())

        self.left_column.addWidget(self.init_atacama_section())
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

        QtCore.QTimer.singleShot(300, self._show_deprecation_warning)

    def _show_deprecation_warning(self):
        QtWidgets.QMessageBox.warning(
            self,
            "Program nie je udržovaný",
            "⚠️ Tento program nie je ďalej udržovaný.\n"
            "Pre pomoc kontaktujte j44soft@gmail.com\n\n"
            "Nová verzia je dostupná na: https://devcontrol2.gitbook.io/devcontrol2"
        )

    def spusti_indistarter_c14(self):
        try:
            out = subprocess.check_output("indistarter", shell=True)
            self.loguj(out.decode())
        except Exception:
            self.loguj_traceback("Chyba spustenia INDISTARTER C14")

    def spusti_indistarter_az2000(self):
        try:
            out = subprocess.check_output(f"ssh {SSH_USER2}@{AZ2000_IP} indistarter", shell=True)
            self.loguj(out.decode())
        except Exception:
            self.loguj_traceback("Chyba INDISTARTER AZ2000")

    def init_atacama_section(self):
        group_box = QtWidgets.QGroupBox("ATACAMA")
        layout = QtWidgets.QGridLayout(group_box)

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
        z1 = QtWidgets.QPushButton("Zapni AZ2000")
        z2 = QtWidgets.QPushButton("Zapni GM3000")
        z1.clicked.connect(lambda: self.wake_on_lan("00:c0:08:a9:c2:32"))
        z2.clicked.connect(lambda: self.wake_on_lan("00:c0:08:aa:35:12"))
        lay.addWidget(z1, 0, 0)
        lay.addWidget(z2, 0, 1)
        return box

    def init_ota_section(self):
        box = QtWidgets.QGroupBox("OTA Aktuializácie a Kamery")
        lay = QtWidgets.QGridLayout(box)

        but = QtWidgets.QPushButton("🔄 Aktualizovať program")
        but.clicked.connect(self.aktualizuj_program)
        lay.addWidget(but, 0, 0, 1, 2)

        control_btn = QtWidgets.QPushButton("🛠️ Control Atacama Camera")
        control_btn.clicked.connect(lambda: subprocess.Popen(["python3", "/home/dpv/j44softapps-socketcontrol/C14-vigi.py"]))
        lay.addWidget(control_btn, 1, 0, 1, 2)

        rtsp_atacama = "rtsp://dpv-hard:lefton44@172.20.20.134:554/stream1"
        rtsp_astrofoto = "rtsp://dpv-hard:lefton44@172.20.20.131:554/stream1"

        kamera_btn1 = QtWidgets.QPushButton("📷 Stream Atacama")
        kamera_btn2 = QtWidgets.QPushButton("📷 Stream Astrofoto")
        kamera_btn1.clicked.connect(lambda: self.spusti_stream_live(rtsp_atacama, self.kamera_label_atacama, "atacama"))
        kamera_btn2.clicked.connect(lambda: self.spusti_stream_live(rtsp_astrofoto, self.kamera_label_astro, "astro"))

        lay.addWidget(kamera_btn1, 2, 0)
        lay.addWidget(kamera_btn2, 2, 1)
        lay.addWidget(self.kamera_label_atacama, 3, 0)
        lay.addWidget(self.kamera_label_astro, 3, 1)

        return box

    def loguj_traceback(self, msg, typ="error"):
        tb = traceback.format_exc()
        self.loguj(f"{msg}\n{tb}" if IS_DEV else msg, typ=typ)

    def spusti_stream_live(self, url: str, label: QtWidgets.QLabel, kamera_typ: str):
        attr = f"rtsp_worker_{kamera_typ}"
        worker = getattr(self, attr, None)
        if worker is not None and worker.isRunning():
            worker.stop()
            label.clear()
            setattr(self, attr, None)
            self.loguj(f"Zastavený RTSP stream: {kamera_typ}", typ="info")
            return
        worker = RtspWorker(url)
        worker.frame_ready.connect(label.setPixmap)
        worker.error_signal.connect(lambda msg: self.loguj(msg, typ="error"))
        worker.finished.connect(label.clear)
        setattr(self, attr, worker)
        worker.start()
        self.loguj(f"Spustený RTSP stream: {kamera_typ}", typ="success")

    def aktualizuj_stav_zasuviek(self):
        for n, c in ZASUVKY.items():
            self.zisti_stav_zasuvky(c, n)

    def ovladaj_zasuvku(self, cis, on, lab):
        cmd = f"sispmctl -{('o' if on else 'f')} {cis}"
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
        except Exception:
            self.loguj_traceback(f"Chyba zisťovania stavu zásuvky {lab}")
            self.status_labels[lab].setPixmap(QtGui.QPixmap("led_def.png"))

    def ovladaj_strechu(self, s):
        PRIKAZY_STRECHA = {
            "sever": ["usbrelay BITFT_2=1", "usbrelay BITFT_2=0"],
            "juh":   ["usbrelay BITFT_1=1", "usbrelay BITFT_1=0"],
            "both":  ["usbrelay BITFT_1=1", "usbrelay BITFT_2=1",
                      "usbrelay BITFT_1=0", "usbrelay BITFT_2=0"],
        }
        prikazy = PRIKAZY_STRECHA.get(s)
        if not prikazy:
            self.loguj(f"Neznámy smer strechy: {s}", typ="error")
            return
        try:
            for pr in prikazy[:len(prikazy)//2]:
                subprocess.run(pr, shell=True, check=True)
            time.sleep(2)
            for pr in prikazy[len(prikazy)//2:]:
                subprocess.run(pr, shell=True, check=True)
            self.loguj(f"Strecha ovládaná ({s})", typ="success")
        except Exception as e:
            if IS_DEV:
                self.loguj(f"Chyba pri ovládaní strechy {s}:\n{traceback.format_exc()}", typ="error")
            else:
                self.loguj(f"Chyba pri ovládaní strechy {s}", typ="error")

    def toggle_casovac_strechy(self, st):
        e = (st == QtCore.Qt.Checked)
        self.cas_smer.setEnabled(e)
        self.cas_input.setEnabled(e)
        self.cas_btn.setEnabled(e)
        if not e:
            self.c_act = False

    def nastav_casovac_strechy(self):
        try:
            naive = datetime.strptime(self.cas_input.text(), "%Y-%m-%d %H:%M")
            local = pytz.timezone("Europe/Bratislava").localize(naive)
            self.c_time = local.astimezone(pytz.utc)
            now_utc = datetime.now(pytz.utc)
            if self.c_time <= now_utc:
                QtWidgets.QMessageBox.warning(self, "Chybný čas", "Zadaný čas je v minulosti. Časovač nebude aktivovaný.")
                self.c_act = False
                return
            self.c_act = True
            self.c_smer = self.cas_smer.currentText()
            self.loguj(f"Časovač nastavený na {self.c_time} pre smer {self.c_smer}", typ="success")
        except Exception:
            self.loguj_traceback("Chybný formát času")

    def skontroluj_cas_strechy(self):
        if self.c_act and datetime.now(pytz.utc) >= self.c_time:
            self.ovladaj_strechu(self.c_smer)
            self.c_act = False
            self.loguj("Strecha aktivovaná časovačom", typ="success")

    def wake_on_lan(self, mac):
        try:
            subprocess.run(["which", "wakeonlan"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            from wakeonlan import send_magic_packet
            send_magic_packet(mac)
            self.loguj(f"WOL packet sent to {mac}", typ="success")
        except subprocess.CalledProcessError:
            self.show_wol_not_supported_dialog()
        except Exception:
            self.loguj_traceback("Chyba WOL")

    def show_wol_not_supported_dialog(self):
        QtWidgets.QMessageBox.critical(self, "WOL not supported", "Wake on LAN is not supported on this OS.")

    def spusti_stream(self, rtsp_url):
        try:
            subprocess.Popen(["ffplay", "-fflags", "nobuffer", "-i", rtsp_url])
            self.loguj(f"Spustený RTSP stream: {rtsp_url}", typ="success")
        except Exception:
            self.loguj_traceback(f"Chyba pri spúštaní streamu {rtsp_url}")

    def aktualizuj_program(self):
        try:
            _prog = str(Path(__file__).resolve())
            curl_cmd = f"curl -fsSL {GITHUB_RAW_URL} -o {_prog}"
            subprocess.run(curl_cmd, shell=True, check=True)
            self.loguj("Program bol úspšne aktualizovaný.")
            QtWidgets.QMessageBox.information(
                self, "OTA Aktuializácia",
                "Program bol aktualizovaný. Reštartujem aplikáciu po zavretí tohto dialógu, "
                "ak nebude úspš naštartujte aplikáciu manuálne."
            )
            subprocess.Popen([sys.executable, _prog])
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            self.loguj_traceback(f"Chyba pri aktuializácii programu: {e}")
        except Exception:
            self.loguj_traceback("Neočakávaná chyba pri aktuializácii")

    def odomkni_editor_funkcii(self):
        pin, ok = QtWidgets.QInputDialog.getText(
            self, "Developer PIN", "Zadaj PIN pre úpravu funkcií:", QtWidgets.QLineEdit.Password
        )
        if ok and pin == "6589":
            editor = QtWidgets.QDialog(self)
            editor.setWindowTitle("Live úprava funkcií")
            editor.resize(800, 500)
            layout = QtWidgets.QVBoxLayout(editor)
            info = QtWidgets.QLabel(
                "Tu môžeš upraviť funkcie `ovladaj_strechu`, `ovladaj_zasuvku` a `aktualizuj_program`.\n"
                "Zmeny sa prejavia po reštarte."
            )
            layout.addWidget(info)
            try:
                _prog = str(Path(__file__).resolve())
                with open(_prog, "r") as f:
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
            _prog = str(Path(__file__).resolve())
            with open(_prog, "w") as f:
                f.write(self.editor_area.toPlainText())
            QtWidgets.QMessageBox.information(
                self, "Hotovo", "Zmeny boli uložené. Program sa teraz reštartuje."
            )
            subprocess.Popen([sys.executable, _prog, "-developer"])
            sys.exit(0)
        except Exception:
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
        self._toasts.append(toast)
        toast.show_()
        self._toasts = [t for t in self._toasts if t.isVisible()]


class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        pix = QtGui.QPixmap("logo.png")
        super().__init__(pix)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        lic = QtWidgets.QLabel(
            "Licensed under the MIT License – see LICENSE file for details.",
            self
        )
        lic.setStyleSheet("color: blue; font-size: 8px;")
        lic.setAlignment(QtCore.Qt.AlignCenter)
        lic.setGeometry(0, pix.height(), pix.width(), 20)

        lbl = QtWidgets.QLabel(
            "Jadiv DEVCONTROL ubunted Enterprise for Vihorlat Observatory",
            self
        )
        lbl.setStyleSheet("color: blue; font-weight: bold; font-size: 10px;")
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
        # Fixed: was 0.50s x 101 iterations = ~50 seconds; now 0.03s = ~3 seconds
        for i in range(101):
            self.pr.setValue(i)
            QtWidgets.qApp.processEvents()
            time.sleep(0.03)


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
            "Pravdepodobne je chyba v aktualizovaném kóde.\n"
            "Ak nieste vývojár kódu obráťte sa na JaPySoft.\n"
        )
        error_label.setStyleSheet("color: red; font-size: 11pt; font-weight: bold;")
        layout.addWidget(error_label)
        error_details = QtWidgets.QTextEdit()
        error_details.setReadOnly(True)
        error_details.setPlainText(str(e))
        layout.addWidget(error_details)

        def spusti_update():
            try:
                _prog = str(Path(__file__).resolve())
                subprocess.run(f"curl -fsSL {GITHUB_RAW_URL} -o {_prog}", shell=True, check=True)
                QtWidgets.QMessageBox.information(bug_window, "Hotovo", "Program bol aktualizovaný. Spušť ho znova.")
                bug_window.close()
            except Exception as ex:
                QtWidgets.QMessageBox.critical(bug_window, "Chyba", f"Zlyhala aktuializácia: {ex}")

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
