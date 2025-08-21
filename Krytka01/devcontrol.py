# PICO strecha – GUI (Splash + Log + 3 tlačidlá + stavová ikonka + časovače)
# Spúšťa ~/pico_open.py, ~/pico_close.py a číta ~/pico-check.py
# Ikonky očakáva vedľa tohto .py: led_def.png, led_green.png, led_red.png

import sys
import subprocess
from pathlib import Path
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets

HOME = Path.home()
APP_DIR = Path(__file__).resolve().parent

PY_OPEN = HOME / "pico_open.py"
PY_CLOSE = HOME / "pico_close.py"
PY_CHECK = HOME / "pico-check.py"

LOG_FILE = HOME / "pico_gui.log"

ICON_DEF = APP_DIR / "led_def.png"
ICON_ON  = APP_DIR / "led_green.png"   # 1 = otvorené
ICON_OFF = APP_DIR / "led_red.png"     # 0 = zatvorené

REFRESH_MS = 3000  # interval kontroly stavu


def run_script(path: Path) -> subprocess.CompletedProcess:
    """Spustí python skript cez aktuálny interpreter (cross-platform)."""
    return subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        check=False
    )


class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        super().__init__()
        self.resize(720, 420)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: white;")

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        # Logo (ak je)
        logo_lbl = QtWidgets.QLabel()
        logo_path = APP_DIR / "logo.png"
        if logo_path.exists():
            pm = QtGui.QPixmap(str(logo_path)).scaled(96, 96, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            logo_lbl.setPixmap(pm)
            logo_lbl.setAlignment(QtCore.Qt.AlignCenter)
            lay.addWidget(logo_lbl)

        title = QtWidgets.QLabel("🛰️ Jadiv DEVCONTROL – PICO Strecha")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("color:#224488; font-weight:bold; font-size:18pt;")
        lay.addWidget(title)

        self.status = QtWidgets.QLabel("Inicializujem…")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.status.setStyleSheet("color:#333; font-size:11pt;")
        lay.addWidget(self.status)

        self.pr = QtWidgets.QProgressBar()
        self.pr.setRange(0, 100)
        self.pr.setValue(0)
        self.pr.setTextVisible(False)
        lay.addWidget(self.pr)

        foot = QtWidgets.QLabel("Licensed under the MIT License – see LICENSE file for details.")
        foot.setAlignment(QtCore.Qt.AlignCenter)
        foot.setStyleSheet("color:#0077cc; font-size:9pt;")
        lay.addWidget(foot)

    def simulate_loading(self, app):
        steps = [
            "Načítavam GUI komponenty…",
            "Kontrolujem súbory pico_open.py / pico_close.py / pico-check.py…",
            "Pripravujem logovanie…",
            "Spúšťam hlavnú aplikáciu…",
        ]
        for i, text in enumerate(steps, start=1):
            self.status.setText(text)
            self.pr.setValue(int(i * 100 / len(steps)))
            app.processEvents()
            QtCore.QThread.msleep(350)


class Toast(QtWidgets.QLabel):
    def __init__(self, msg, kind="info", parent=None):
        super().__init__(msg, parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        bg = {"success": "#135b13", "error": "#dc2525", "info": "#b9e9f1"}.get(kind, "#b9e9f1")
        fg = {"success": "#155724", "error": "#721c24", "info": "#050c4d"}.get(kind, "#050c4d")
        self.setStyleSheet(f"QLabel{{background:{bg};color:{fg};border:2px solid black;border-radius:10px;padding:8px;font-size:10pt;}}")
        self.adjustSize()
        QtCore.QTimer.singleShot(2200, self.close)

    def show_(self):
        # pravý spodný roh primárnej obrazovky
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.bottom() - self.height() - 20)
        self.show()


class Main(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PICO strecha – jednoduché ovládanie")
        self.resize(640, 520)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)

        # horný riadok: 3 tlačidlá + ikona
        top = QtWidgets.QHBoxLayout()
        self.btn_open  = QtWidgets.QPushButton("🔓 Otvoriť (pico_open.py)")
        self.btn_close = QtWidgets.QPushButton("🔒 Zatvoriť (pico_close.py)")
        self.btn_check = QtWidgets.QPushButton("🔄 Skontrolovať stav")

        self.btn_open.clicked.connect(self.cmd_open)
        self.btn_close.clicked.connect(self.cmd_close)
        self.btn_check.clicked.connect(self.refresh_state)

        self.icon_lbl = QtWidgets.QLabel()
        self.icon_lbl.setFixedSize(36, 36)
        self.icon_lbl.setScaledContents(True)
        self._set_icon(ICON_DEF)

        top.addWidget(self.btn_open)
        top.addWidget(self.btn_close)
        top.addWidget(self.btn_check)
        top.addStretch()
        top.addWidget(self.icon_lbl)

        # === ČASOVAČE ===
        sched_box = QtWidgets.QGroupBox("Časovač")
        sched_lay = QtWidgets.QGridLayout(sched_box)

        # Otvorenie
        self.chk_open = QtWidgets.QCheckBox("Aktivovať otvorenie v čase:")
        self.dt_open  = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.dt_open.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dt_open.setCalendarPopup(True)
        self.btn_set_open = QtWidgets.QPushButton("Nastaviť otvorenie")
        self.lbl_open_status = QtWidgets.QLabel("Neplánované")

        self.btn_set_open.clicked.connect(self.set_open_schedule)
        self.chk_open.stateChanged.connect(self.toggle_open_enabled)

        # Zatvorenie
        self.chk_close = QtWidgets.QCheckBox("Aktivovať zatvorenie v čase:")
        self.dt_close  = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.dt_close.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dt_close.setCalendarPopup(True)
        self.btn_set_close = QtWidgets.QPushButton("Nastaviť zatvorenie")
        self.lbl_close_status = QtWidgets.QLabel("Neplánované")

        self.btn_set_close.clicked.connect(self.set_close_schedule)
        self.chk_close.stateChanged.connect(self.toggle_close_enabled)

        # Rozloženie časovača
        r = 0
        sched_lay.addWidget(self.chk_open, r, 0, 1, 2); sched_lay.addWidget(self.dt_open, r, 2); sched_lay.addWidget(self.btn_set_open, r, 3); r += 1
        sched_lay.addWidget(QtWidgets.QLabel("Stav:"), r, 0); sched_lay.addWidget(self.lbl_open_status, r, 1, 1, 3); r += 1
        sched_lay.addWidget(self.chk_close, r, 0, 1, 2); sched_lay.addWidget(self.dt_close, r, 2); sched_lay.addWidget(self.btn_set_close, r, 3); r += 1
        sched_lay.addWidget(QtWidgets.QLabel("Stav:"), r, 0); sched_lay.addWidget(self.lbl_close_status, r, 1, 1, 3)

        self.toggle_open_enabled(self.chk_open.checkState())
        self.toggle_close_enabled(self.chk_close.checkState())

        # log okno
        self.log = QtWidgets.QTextEdit(readOnly=True)
        self.log.setMinimumHeight(220)

        root.addLayout(top)
        root.addWidget(sched_box)
        root.addWidget(self.log)

        # načítaj existujúci log
        try:
            if LOG_FILE.exists():
                self.log.setPlainText(LOG_FILE.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            pass

        # auto-refresh stavu každé 3 sekundy
        self._last_state = None  # None/0/1
        self.timer_state = QtCore.QTimer(self)
        self.timer_state.timeout.connect(self.refresh_state)
        self.timer_state.start(REFRESH_MS)

        # plánovač – kontrola každú sekundu
        self.open_active = False
        self.open_when: QtCore.QDateTime | None = None
        self.close_active = False
        self.close_when: QtCore.QDateTime | None = None

        self.timer_sched = QtCore.QTimer(self)
        self.timer_sched.timeout.connect(self._scheduler_tick)
        self.timer_sched.start(1000)

        # prvé zistenie po štarte
        QtCore.QTimer.singleShot(400, self.refresh_state)

    # ----- helpers -----
    def _set_icon(self, path: Path):
        pm = QtGui.QPixmap(str(path))
        if pm.isNull():
            # fallback šedý štvorec
            pm = QtGui.QPixmap(36, 36)
            pm.fill(QtGui.QColor("#888"))
        self.icon_lbl.setPixmap(pm)

    def _log(self, msg: str, kind: str = "info", toast: bool = True):
        t = datetime.now().strftime("%H:%M:%S")
        line = f"[{t}] {msg}"
        self.log.append(line)
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
        if toast:
            Toast(msg, kind, self).show_()

    def _run_and_report(self, path: Path, action_name: str):
        if not path.exists():
            self._log(f"Chýba súbor: {path}", "error")
            return False
        proc = run_script(path)
        if proc.returncode == 0:
            self._log(f"OK: {action_name}", "success")
            return True
        else:
            err = (proc.stderr or proc.stdout or "").strip()
            self._log(f"Chyba {action_name}: {err}", "error")
            return False

    # ----- akcie tlačidiel -----
    def cmd_open(self):
        if self._run_and_report(PY_OPEN, "Otvoriť (pico_open.py)"):
            self.refresh_state()

    def cmd_close(self):
        if self._run_and_report(PY_CLOSE, "Zatvoriť (pico_close.py)"):
            self.refresh_state()

    # ----- stav ikonky -----
    def refresh_state(self):
        if not PY_CHECK.exists():
            if self._last_state is not None:
                self._set_icon(ICON_DEF)
                self._log(f"Chýba súbor: {PY_CHECK}", "error", toast=False)
                self._last_state = None
            return

        proc = run_script(PY_CHECK)
        out = (proc.stdout or "").strip()
        if proc.returncode != 0:
            if self._last_state is not None:
                self._set_icon(ICON_DEF)
                self._log(f"Chyba check: {(proc.stderr or out).strip()}", "error", toast=False)
                self._last_state = None
            return

        if out == "1":
            if self._last_state != 1:
                self._set_icon(ICON_ON)
                self._log("Stav: OTVORENÉ (1)", "success", toast=False)
                self._last_state = 1
        elif out == "0":
            if self._last_state != 0:
                self._set_icon(ICON_OFF)
                self._log("Stav: ZATVORENÉ (0)", "info", toast=False)
                self._last_state = 0
        else:
            if self._last_state is not None:
                self._set_icon(ICON_DEF)
                self._log(f"Neznámy výstup z pico-check.py: '{out}'", "error", toast=False)
                self._last_state = None

    # ----- časovače UI -----
    def toggle_open_enabled(self, state):
        en = state == QtCore.Qt.Checked
        self.dt_open.setEnabled(en)
        self.btn_set_open.setEnabled(en)

    def toggle_close_enabled(self, state):
        en = state == QtCore.Qt.Checked
        self.dt_close.setEnabled(en)
        self.btn_set_close.setEnabled(en)

    def set_open_schedule(self):
        if not self.chk_open.isChecked():
            self.open_active = False
            self.lbl_open_status.setText("Neplánované")
            self._log("Časovač otvorenia vypnutý.", "info", toast=False)
            return

        when = self.dt_open.dateTime()
        if when <= QtCore.QDateTime.currentDateTime():
            self._log("Časovač otvorenia: zadaný čas je v minulosti.", "error")
            return

        self.open_when = when
        self.open_active = True
        self.lbl_open_status.setText(f"Naplánované na {when.toString('yyyy-MM-dd HH:mm')}")

        self._log(f"Časovač otvorenia nastavený na {when.toString('yyyy-MM-dd HH:mm')}.", "success")

    def set_close_schedule(self):
        if not self.chk_close.isChecked():
            self.close_active = False
            self.lbl_close_status.setText("Neplánované")
            self._log("Časovač zatvorenia vypnutý.", "info", toast=False)
            return

        when = self.dt_close.dateTime()
        if when <= QtCore.QDateTime.currentDateTime():
            self._log("Časovač zatvorenia: zadaný čas je v minulosti.", "error")
            return

        self.close_when = when
        self.close_active = True
        self.lbl_close_status.setText(f"Naplánované na {when.toString('yyyy-MM-dd HH:mm')}")

        self._log(f"Časovač zatvorenia nastavený na {when.toString('yyyy-MM-dd HH:mm')}.", "success")

    # ----- plánovač tick -----
    def _scheduler_tick(self):
        now = QtCore.QDateTime.currentDateTime()

        if self.open_active and self.open_when and now >= self.open_when:
            self._log("Časovač: spúšťam OTVORIŤ.", "info")
            self.cmd_open()
            self.open_active = False
            self.lbl_open_status.setText("Neplánované")

        if self.close_active and self.close_when and now >= self.close_when:
            self._log("Časovač: spúšťam ZATVORIŤ.", "info")
            self.cmd_close()
            self.close_active = False
            self.lbl_close_status.setText("Neplánované")


def main():
    app = QtWidgets.QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    app.processEvents()
    splash.simulate_loading(app)

    w = Main()
    w.show()
    splash.finish(w)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
