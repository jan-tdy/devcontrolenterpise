# Jadiv DEVCONTROL – Telescope Cover GUI
# Controls a motorised dome cover via a Raspberry Pi Pico running main.py.
# Expected script locations: ~/pico_open.py, ~/pico_close.py, ~/pico-check.py
# Expected assets next to this file: led_def.png, led_green.png, led_red.png, logo.png

import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime

import requests
from PyQt5 import QtCore, QtGui, QtWidgets

CURRENT_VERSION = "2026.6_1.0"
# TODO: update this URL after Krytka01 moves to its own repository
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main"
    "/Krytka01/devcontrol.py"
)

HOME    = Path.home()
APP_DIR = Path(__file__).resolve().parent

PY_OPEN  = HOME / "pico_open.py"
PY_CLOSE = HOME / "pico_close.py"
PY_CHECK = HOME / "pico-check.py"

LOG_FILE = HOME / "pico_gui.log"

ICON_DEF = APP_DIR / "led_def.png"
ICON_ON  = APP_DIR / "led_green.png"   # state 1 = open
ICON_OFF = APP_DIR / "led_red.png"     # state 0 = closed

REFRESH_MS = 3000


def run_script(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


# ── OTA ──────────────────────────────────────────────────────────────────────

class UpdateWorker(QtCore.QThread):
    update_available = QtCore.pyqtSignal(str)

    def run(self):
        try:
            res = requests.get(GITHUB_RAW_URL, timeout=5)
            if res.status_code == 200:
                match = re.search(r'CURRENT_VERSION\s*=\s*"([\d._]+)"', res.text)
                if match and match.group(1) != CURRENT_VERSION:
                    self.update_available.emit(res.text)
        except Exception:
            pass


# ── Splash ───────────────────────────────────────────────────────────────────

class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        super().__init__()
        self.resize(720, 420)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint
        )
        self.setStyleSheet("background-color: #ffffff;")

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(14)

        logo_lbl = QtWidgets.QLabel()
        logo_path = APP_DIR / "logo.png"
        if logo_path.exists():
            pm = QtGui.QPixmap(str(logo_path)).scaled(
                96, 96,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
            logo_lbl.setPixmap(pm)
            logo_lbl.setAlignment(QtCore.Qt.AlignCenter)
            lay.addWidget(logo_lbl)

        title = QtWidgets.QLabel(
            f"🛰️  Jadiv DEVCONTROL – Telescope Cover  v{CURRENT_VERSION}"
        )
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet(
            "color:#1d4ed8; font-weight:bold; font-size:18pt; font-family:'Segoe UI';"
        )
        lay.addWidget(title)

        self.status = QtWidgets.QLabel("Initialising…")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.status.setStyleSheet("color:#374151; font-size:11pt;")
        lay.addWidget(self.status)

        self.pr = QtWidgets.QProgressBar()
        self.pr.setRange(0, 100)
        self.pr.setValue(0)
        self.pr.setTextVisible(False)
        self.pr.setStyleSheet(
            "QProgressBar{border:1px solid #d1d5db;border-radius:6px;background:#f3f4f6;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:5px;}"
        )
        lay.addWidget(self.pr)

        foot = QtWidgets.QLabel(
            "Licensed under the MIT License – see LICENSE for details.   |   j44soft@gmail.com"
        )
        foot.setAlignment(QtCore.Qt.AlignCenter)
        foot.setStyleSheet("color:#6b7280; font-size:8pt;")
        lay.addWidget(foot)

    def simulate_loading(self, app):
        steps = [
            "Loading GUI components…",
            "Locating pico_open.py / pico_close.py / pico-check.py…",
            "Preparing logging…",
            "Starting main application…",
        ]
        for i, text in enumerate(steps, start=1):
            self.status.setText(text)
            self.pr.setValue(int(i * 100 / len(steps)))
            app.processEvents()
            QtCore.QThread.msleep(350)


# ── Toast notification ───────────────────────────────────────────────────────────

class Toast(QtWidgets.QLabel):
    _STYLE = {
        "success": "border:2px solid #166534;background:#dcfce7;color:#14532d;",
        "error":   "border:2px solid #991b1b;background:#fee2e2;color:#7f1d1d;",
        "info":    "border:2px solid #1e40af;background:#dbeafe;color:#1e3a8a;",
    }

    def __init__(self, msg: str, kind: str = "info", parent=None):
        super().__init__(msg, parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        style = self._STYLE.get(kind, self._STYLE["info"])
        self.setStyleSheet(
            f"QLabel{{{style}border-radius:10px;padding:8px 14px;font-size:10pt;}}"
        )
        self.adjustSize()
        QtCore.QTimer.singleShot(2500, self.close)

    def show_(self):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.bottom() - self.height() - 20)
        self.show()


# ── Main window ───────────────────────────────────────────────────────────────────

class Main(QtWidgets.QMainWindow):
    _SB_STYLE = {
        "open":    "background:#166534;color:#ffffff;font-weight:bold;padding:2px 6px;",
        "closed":  "background:#7f1d1d;color:#ffffff;font-weight:bold;padding:2px 6px;",
        "unknown": "background:#374151;color:#ffffff;font-weight:bold;padding:2px 6px;",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🛰️  Jadiv DEVCONTROL – Telescope Cover  v{CURRENT_VERSION}")
        self.resize(700, 580)

        logo_path = APP_DIR / "logo.png"
        if logo_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(logo_path)))

        self._toasts: list = []
        self._last_state = None   # None / 0 / 1

        # ── Central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(8)

        # ── Button row
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(8)

        self.btn_open = QtWidgets.QPushButton("🔓  Open Cover")
        self.btn_open.setMinimumHeight(40)
        self.btn_open.setStyleSheet(
            "QPushButton{border:2px solid #16a34a;border-radius:7px;padding:4px 14px;"
            "font-size:11pt;font-weight:bold;}"
            "QPushButton:hover{background:#dcfce7;}"
            "QPushButton:disabled{border-color:#6b7280;color:#9ca3af;}"
        )

        self.btn_close = QtWidgets.QPushButton("🔒  Close Cover")
        self.btn_close.setMinimumHeight(40)
        self.btn_close.setStyleSheet(
            "QPushButton{border:2px solid #dc2626;border-radius:7px;padding:4px 14px;"
            "font-size:11pt;font-weight:bold;}"
            "QPushButton:hover{background:#fee2e2;}"
            "QPushButton:disabled{border-color:#6b7280;color:#9ca3af;}"
        )

        self.btn_check = QtWidgets.QPushButton("🔄  Refresh")
        self.btn_check.setMinimumHeight(40)
        self.btn_check.setStyleSheet(
            "QPushButton{border:1px solid #9ca3af;border-radius:7px;padding:4px 10px;}"
            "QPushButton:hover{background:#f3f4f6;}"
        )

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

        # ── Scheduler
        sched_box = QtWidgets.QGroupBox("Scheduler")
        sched_lay = QtWidgets.QGridLayout(sched_box)
        sched_lay.setColumnStretch(1, 1)

        self.chk_open        = QtWidgets.QCheckBox("Schedule OPEN at:")
        self.dt_open         = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.dt_open.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dt_open.setCalendarPopup(True)
        self.btn_set_open    = QtWidgets.QPushButton("Set")
        self.lbl_open_status = QtWidgets.QLabel("Not scheduled")
        self.lbl_open_status.setStyleSheet("color:#6b7280;font-style:italic;")

        self.chk_close        = QtWidgets.QCheckBox("Schedule CLOSE at:")
        self.dt_close         = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.dt_close.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dt_close.setCalendarPopup(True)
        self.btn_set_close    = QtWidgets.QPushButton("Set")
        self.lbl_close_status = QtWidgets.QLabel("Not scheduled")
        self.lbl_close_status.setStyleSheet("color:#6b7280;font-style:italic;")

        self.btn_set_open.clicked.connect(self.set_open_schedule)
        self.btn_set_close.clicked.connect(self.set_close_schedule)
        self.chk_open.stateChanged.connect(self.toggle_open_enabled)
        self.chk_close.stateChanged.connect(self.toggle_close_enabled)

        sched_lay.addWidget(self.chk_open,          0, 0)
        sched_lay.addWidget(self.dt_open,           0, 1)
        sched_lay.addWidget(self.btn_set_open,      0, 2)
        sched_lay.addWidget(self.lbl_open_status,   0, 3)
        sched_lay.addWidget(self.chk_close,         1, 0)
        sched_lay.addWidget(self.dt_close,          1, 1)
        sched_lay.addWidget(self.btn_set_close,     1, 2)
        sched_lay.addWidget(self.lbl_close_status,  1, 3)

        self.toggle_open_enabled(QtCore.Qt.Unchecked)
        self.toggle_close_enabled(QtCore.Qt.Unchecked)

        # ── Log area
        log_box = QtWidgets.QGroupBox("Activity Log")
        log_lay = QtWidgets.QVBoxLayout(log_box)
        log_lay.setContentsMargins(6, 6, 6, 6)

        self.log = QtWidgets.QTextEdit(readOnly=True)
        self.log.setFont(QtGui.QFont("Monospace", 9))
        self.log.setMinimumHeight(200)
        self.log.setStyleSheet(
            "QTextEdit{background:#0f172a;border:1px solid #334155;border-radius:4px;}"
        )
        log_lay.addWidget(self.log)

        root.addLayout(top)
        root.addWidget(sched_box)
        root.addWidget(log_box)

        # Load existing log
        try:
            if LOG_FILE.exists():
                for line in LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
                    self.log.append(f'<span style="color:#64748b">{line}</span>')
        except Exception:
            pass

        # ── Status bar
        self._sb_label = QtWidgets.QLabel("Cover: UNKNOWN")
        self._sb_label.setContentsMargins(4, 0, 4, 0)
        self.statusBar().addWidget(self._sb_label, 1)
        self._update_status_bar("unknown")

        # ── Menu bar
        ota_action = QtWidgets.QAction("Check for Updates…", self)
        ota_action.triggered.connect(self._check_updates)
        about_action = QtWidgets.QAction("About", self)
        about_action.triggered.connect(self._show_about)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(ota_action)
        help_menu.addSeparator()
        help_menu.addAction(about_action)

        # ── Timers & state
        self.open_active  = False
        self.open_when:  QtCore.QDateTime | None = None
        self.close_active = False
        self.close_when: QtCore.QDateTime | None = None

        self.timer_state = QtCore.QTimer(self)
        self.timer_state.timeout.connect(self.refresh_state)
        self.timer_state.start(REFRESH_MS)

        self.timer_sched = QtCore.QTimer(self)
        self.timer_sched.timeout.connect(self._scheduler_tick)
        self.timer_sched.start(1000)

        QtCore.QTimer.singleShot(400, self.refresh_state)

        # Background OTA check
        self._up_worker = UpdateWorker(self)
        self._up_worker.update_available.connect(self._prompt_update)
        self._up_worker.start()

    # ── Status bar

    def _update_status_bar(self, state: str):
        labels = {
            "open":    "●  Cover: OPEN",
            "closed":  "●  Cover: CLOSED",
            "unknown": "●  Cover: UNKNOWN",
        }
        self._sb_label.setText(labels.get(state, labels["unknown"]))
        self.statusBar().setStyleSheet(
            "QStatusBar{" + self._SB_STYLE.get(state, self._SB_STYLE["unknown"]) + "}"
        )

    # ── Icon

    def _set_icon(self, path: Path):
        pm = QtGui.QPixmap(str(path))
        if pm.isNull():
            pm = QtGui.QPixmap(36, 36)
            pm.fill(QtGui.QColor("#6b7280"))
        self.icon_lbl.setPixmap(pm)

    # ── Log

    def _log(self, msg: str, kind: str = "info", toast: bool = True):
        t = datetime.now().strftime("%H:%M:%S")
        line = f"[{t}] {msg}"
        _colors = {"success": "#4ade80", "error": "#f87171", "info": "#94a3b8"}
        color = _colors.get(kind, _colors["info"])
        self.log.append(f'<span style="color:{color};">{line}</span>')
        self.log.moveCursor(QtGui.QTextCursor.End)
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
        if toast:
            t_widget = Toast(msg, kind, self)
            self._toasts.append(t_widget)
            t_widget.show_()
            self._toasts = [t for t in self._toasts if t.isVisible()]

    # ── Script runner

    def _run_and_report(self, path: Path, action_name: str) -> bool:
        if not path.exists():
            self._log(f"Missing file: {path}", "error")
            return False
        proc = run_script(path)
        if proc.returncode == 0:
            self._log(f"OK: {action_name}", "success")
            return True
        err = (proc.stderr or proc.stdout or "").strip()
        self._log(f"Error – {action_name}: {err}", "error")
        return False

    # ── Button actions

    def cmd_open(self):
        if self._run_and_report(PY_OPEN, "Open cover"):
            self.refresh_state()

    def cmd_close(self):
        if self._run_and_report(PY_CLOSE, "Close cover"):
            self.refresh_state()

    # ── State polling

    def refresh_state(self):
        if not PY_CHECK.exists():
            if self._last_state is not None:
                self._set_icon(ICON_DEF)
                self._log(f"Missing file: {PY_CHECK}", "error", toast=False)
                self._last_state = None
                self._update_status_bar("unknown")
                self._sync_buttons(None)
            return

        proc = run_script(PY_CHECK)
        out  = (proc.stdout or "").strip()

        if proc.returncode != 0:
            if self._last_state is not None:
                self._set_icon(ICON_DEF)
                self._log(f"Check error: {(proc.stderr or out).strip()}", "error", toast=False)
                self._last_state = None
                self._update_status_bar("unknown")
                self._sync_buttons(None)
            return

        if out == "1":
            if self._last_state != 1:
                self._set_icon(ICON_ON)
                self._log("State: OPEN (1)", "success", toast=False)
                self._last_state = 1
                self._update_status_bar("open")
                self._sync_buttons(1)
        elif out == "0":
            if self._last_state != 0:
                self._set_icon(ICON_OFF)
                self._log("State: CLOSED (0)", "info", toast=False)
                self._last_state = 0
                self._update_status_bar("closed")
                self._sync_buttons(0)
        else:
            if self._last_state is not None:
                self._set_icon(ICON_DEF)
                self._log(f"Unknown output from pico-check.py: '{out}'", "error", toast=False)
                self._last_state = None
                self._update_status_bar("unknown")
                self._sync_buttons(None)

    def _sync_buttons(self, state):
        self.btn_open.setEnabled(state != 1)
        self.btn_close.setEnabled(state != 0)

    # ── Scheduler

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
            self.lbl_open_status.setText("Not scheduled")
            self.lbl_open_status.setStyleSheet("color:#6b7280;font-style:italic;")
            return
        when = self.dt_open.dateTime()
        if when <= QtCore.QDateTime.currentDateTime():
            self._log("Open scheduler: time is in the past.", "error")
            return
        self.open_when   = when
        self.open_active = True
        ts = when.toString("yyyy-MM-dd HH:mm")
        self.lbl_open_status.setText(f"⏰ Scheduled: {ts}")
        self.lbl_open_status.setStyleSheet("color:#16a34a;font-weight:bold;")
        self._log(f"Open scheduler set for {ts}.", "success")

    def set_close_schedule(self):
        if not self.chk_close.isChecked():
            self.close_active = False
            self.lbl_close_status.setText("Not scheduled")
            self.lbl_close_status.setStyleSheet("color:#6b7280;font-style:italic;")
            return
        when = self.dt_close.dateTime()
        if when <= QtCore.QDateTime.currentDateTime():
            self._log("Close scheduler: time is in the past.", "error")
            return
        self.close_when   = when
        self.close_active = True
        ts = when.toString("yyyy-MM-dd HH:mm")
        self.lbl_close_status.setText(f"⏰ Scheduled: {ts}")
        self.lbl_close_status.setStyleSheet("color:#dc2626;font-weight:bold;")
        self._log(f"Close scheduler set for {ts}.", "success")

    def _scheduler_tick(self):
        now = QtCore.QDateTime.currentDateTime()
        if self.open_active and self.open_when and now >= self.open_when:
            self._log("Scheduler: triggering OPEN.", "info")
            self.cmd_open()
            self.open_active = False
            self.lbl_open_status.setText("Not scheduled")
            self.lbl_open_status.setStyleSheet("color:#6b7280;font-style:italic;")
        if self.close_active and self.close_when and now >= self.close_when:
            self._log("Scheduler: triggering CLOSE.", "info")
            self.cmd_close()
            self.close_active = False
            self.lbl_close_status.setText("Not scheduled")
            self.lbl_close_status.setStyleSheet("color:#6b7280;font-style:italic;")

    # ── OTA

    def _check_updates(self):
        self._log("Checking for updates…", "info", toast=False)
        worker = UpdateWorker(self)
        worker.update_available.connect(self._prompt_update)
        worker.finished.connect(
            lambda: self._log("Update check complete.", "info", toast=False)
        )
        worker.start()
        self._up_worker = worker

    def _prompt_update(self, new_code: str):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Update available",
            "A newer version is available on GitHub.\nUpdate and restart?",
        )
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                Path(__file__).resolve().write_text(new_code, encoding="utf-8")
                QtWidgets.QMessageBox.information(
                    self,
                    "Updated",
                    "Update applied. Please restart the application.",
                )
                sys.exit(0)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Update failed", str(e))

    def _show_about(self):
        QtWidgets.QMessageBox.information(
            self,
            "About – Jadiv DEVCONTROL",
            f"Jadiv DEVCONTROL – Motorised Telescope Cover\n"
            f"Version: {CURRENT_VERSION}\n\n"
            f"Controls a motorised dome/cover via a Raspberry Pi Pico\n"
            f"over serial USB using MicroPython firmware.\n\n"
            f"Contact:  j44soft@gmail.com\n"
            f"License:  MIT",
        )


# ── Entry point

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
