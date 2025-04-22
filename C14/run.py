import subprocess
import sys
import time
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog, QProgressDialog

C14_PATH = "/home/dpv/j44softapps-socketcontrol/C14.py"
C14_URL = "https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py"

def show_choice_dialog():
    items = [
        "Classic boot (odporúčané)",
        "Developer boot (bez aktualizácie)",
        "Developer boot s aktualizáciou"
    ]
    choice, ok = QInputDialog.getItem(
        None,
        "DEVCONTROL – režim štartu",
        "Niekedy štartovanie najnovšej verzie spôsobí downgrade.\n\nProsím zvoľte spôsob štartu:",
        items,
        0,
        False
    )
    return choice if ok else None

def show_progress(title, text):
    dlg = QProgressDialog(text, None, 0, 100)
    dlg.setWindowTitle(title)
    dlg.setWindowModality(True)
    dlg.setMinimumWidth(400)
    dlg.setValue(0)
    for i in range(101):
        dlg.setValue(i)
        QApplication.processEvents()
        time.sleep(0.016)
    dlg.close()

def download_new_C14():
    try:
        # zálohovanie
        if os.path.exists(C14_PATH):
            n = 1
            while os.path.exists(f"/home/dpv/j44softapps-socketcontrol/C14-old{n}.py"):
                n += 1
            os.rename(C14_PATH, f"/home/dpv/j44softapps-socketcontrol/C14-old{n}.py")
        subprocess.check_call([
            "curl", "-fsSL", C14_URL, "-o", C14_PATH
        ])
        return True
    except Exception as e:
        QMessageBox.critical(None, "Chyba OTA", f"Zlyhala aktualizácia:\n{e}")
        return False

def start_script(developer=False):
    if developer:
        subprocess.Popen(["python3", C14_PATH, "-developer"])
    else:
        subprocess.Popen(["python3", C14_PATH])

def kill_previous():
    subprocess.call(["pkill", "-f", "python3 /home/dpv/j44softapps-socketcontrol/C14.py"])

def main():
    app = QApplication(sys.argv)

    choice = show_choice_dialog()
    if not choice:
        sys.exit(0)

    kill_previous()

    if choice == "Developer boot (bez aktualizácie)":
        QMessageBox.information(None, "DEVCONTROL", "Štartujem bez OTA update...")
        start_script(developer=True)

    elif choice == "Developer boot s aktualizáciou":
        show_progress("DEVCONTROL - OTA", "Sťahujem najnovšiu verziu...")
        if download_new_C14():
            start_script(developer=True)

    else:  # Classic boot
        show_progress("DEVCONTROL - Štart", "Štartujem najnovšiu verziu...")
        if download_new_C14():
            start_script(developer=False)

    sys.exit(0)

if __name__ == "__main__":
    main()
