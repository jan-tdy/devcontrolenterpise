# PICO strecha – minimal GUI (Splash + Log + 3 tlačidlá + stavová ikonka)
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

        title = QtWidgets.QLabel("🛰️ Jadiv DEVCONTROL –  ovaldanie krytky - free version")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("color:#224488; font-weight:bold; font-size:18pt;")
        lay.addWidget(title)

        self.status = QtWidgets.QLabel("Inicializujem 🛰️ Jadiv DEVCONTROL –  ovaldanie krytky - free version…")
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
        self.setWindowTitle("japysoft krytka - jednoduchy devcontrol")
        self.resize(560, 380)

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

        # log okno
        self.log = QtWidgets.QTextEdit(readOnly=True)
        self.log.setMinimumHeight(220)

        root.addLayout(top)
        root.addWidget(self.log)

        # načítaj existujúci log
        try:
            if LOG_FILE.exists():
                self.log.setPlainText(LOG_FILE.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            pass

        # auto-refresh každé 3 sekundy
        self._last_state = None  # None/0/1
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_state)
        self.timer.start(REFRESH_MS)

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
            return
        proc = run_script(path)
        if proc.returncode == 0:
            self._log(f"OK: {action_name}", "success")
        else:
            err = (proc.stderr or proc.stdout or "").strip()
            self._log(f"Chyba {action_name}: {err}", "error")

    # ----- actions -----
    def cmd_open(self):
        self._run_and_report(PY_OPEN, "Otvoriť (pico_open.py)")
        self.refresh_state()

    def cmd_close(self):
        self._run_and_report(PY_CLOSE, "Zatvoriť (pico_close.py)")
        self.refresh_state()

    def refresh_state(self):
        if not PY_CHECK.exists():
            self._set_icon(ICON_DEF)
            if self._last_state is not None:  # logni len pri zmene z „máme stav“ -> „skript chýba“
                self._log(f"Chýba súbor: {PY_CHECK}", "error")
                self._last_state = None
            return

        proc = run_script(PY_CHECK)
        out = (proc.stdout or "").strip()
        if proc.returncode != 0:
            self._set_icon(ICON_DEF)
            if self._last_state is not None:  # logni len pri zmene
                self._log(f"Chyba check: {(proc.stderr or out).strip()}", "error")
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
                self._log(f"Neznámy výstup z pico-check.py: '{out}'", "error")
                self._last_state = None


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
