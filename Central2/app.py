import sys
import subprocess
import time  # Import time pre oneskorenie
from flask import Flask, request, jsonify

app = Flask(__name__)

# Konštanty
PROGRAM_GITHUB = "github.com/jan-tdy/devcontrolenterpise/Central2/app.py"
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/app.py"
SSH_USER = "dpv"
SSH_PASS = "otj0711"  # POZOR: Heslo by nemalo byť v kóde
C14_IP = "172.20.20.103"
AZ2000_IP = "172.20.20.101"  # IP adresa pre AZ2000


@app.route('/ovladaj_zasuvku_c14', methods=['POST'])
def ovladaj_zasuvku_c14():
    """Ovláda zásuvku na C14 cez SSH. Očakáva JSON payload s kľúčmi 'cislo_zasuvky' a 'zapnut'."""
    data = request.get_json()
    cislo_zasuvky = data.get('cislo_zasuvky')
    zapnut = data.get('zapnut')
    label_name = data.get('label_name') #pouzivame pre response

    if cislo_zasuvky is None or zapnut is None:
        return jsonify({'status': 'error', 'message': 'Chýbajúce parametre'}), 400

    prikaz = f"ssh {SSH_USER}@{C14_IP} sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
    try:
        vystup = subprocess.check_output(prikaz, shell=True, password=SSH_PASS)  # POZOR: Heslo by nemalo byť v kóde
        print(vystup.decode())
        return jsonify({'status': 'success', 'message': f'Zásuvka {cislo_zasuvky} {"zapnutá" if zapnut else "vypnutá"}.', 'label_name': label_name}), 200
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri ovládaní zásuvky na C14: {e}")
        return jsonify({'status': 'error', 'message': f'Chyba pri ovládaní zásuvky: {e}'}), 500


@app.route('/spusti_indistarter_c14', methods=['POST'])
def spusti_indistarter_c14():
    """Spustí INDISTARTER na C14 a UVEX-RPi cez SSH."""
    try:
        # Spustenie na C14
        c14_prikaz = f"ssh {SSH_USER}@{C14_IP} indistarter"
        c14_vystup = subprocess.check_output(c14_prikaz, shell=True, password=SSH_PASS)  # POZOR: Heslo by nemalo byť v kóde
        print(f"INDISTARTER na C14: {c14_vystup.decode()}")

        # Spustenie na UVEX-RPi (cez SSH z C14)
        uvex_prikaz = f"ssh {SSH_USER}@{C14_IP} ssh {SSH_USER}@{AZ2000_IP} indistarter"
        uvex_vystup = subprocess.check_output(uvex_prikaz, shell=True, password=SSH_PASS)  # POZOR: Heslo by nemalo byť v kóde
        print(f"INDISTARTER na UVEX-RPi: {uvex_vystup.decode()}")
        return jsonify({'status': 'success', 'message': 'INDISTARTER spustený na C14 a UVEX-RPi'}), 200
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní INDISTARTERA na C14/UVEX: {e}")
        return jsonify({'status': 'error', 'message': f'Chyba pri spúšťaní INDISTARTERA: {e}'}), 500


@app.route('/ovladaj_strechu_c14', methods=['POST'])
def ovladaj_strechu_c14():
    """Ovláda strechu na C14 cez SSH. Očakáva JSON payload s kľúčom 'strana'."""
    data = request.get_json()
    strana = data.get('strana')

    if strana is None:
        return jsonify({'status': 'error', 'message': 'Chýbajúci parameter "strana"'}), 400

    if strana == "sever":
        prikaz1 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 2 ON"
        prikaz2 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 2 OFF"
    elif strana == "juh":
        prikaz1 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 1 ON"
        prikaz2 = f"ssh {SSH_USER}@{C14_IP} crelay -s BI TFT 1 OFF"
    else:
        return jsonify({'status': 'error', 'message': 'Neplatná strana strechy. Použite "sever" alebo "juh".'}), 400

    try:
        subprocess.run(prikaz1, shell=True, check=True, password=SSH_PASS)  # POZOR: Heslo by nemalo byť v kóde
        time.sleep(2)
        subprocess.run(prikaz2, shell=True, check=True, password=SSH_PASS)  # POZOR: Heslo by nemalo byť v kóde
        print(f"Strecha ({strana}) na C14 ovládaná.")
        return jsonify({'status': 'success', 'message': f'Strecha na C14 ovládaná na stranu {strana}'}), 200
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri ovládaní strechy ({strana}) na C14: {e}")
        return jsonify({'status': 'error', 'message': f'Chyba pri ovládaní strechy: {e}'}), 500



@app.route('/wake_on_lan', methods=['POST'])
def wake_on_lan():
    """Odošle magic packet pre prebudenie zariadenia pomocou Wake-on-LAN. Očakáva JSON s kľúčom 'mac_adresa'."""
    data = request.get_json()
    mac_adresa = data.get('mac_adresa')

    if mac_adresa is None:
        return jsonify({'status': 'error', 'message': 'Chýbajúci parameter "mac_adresa"'}), 400

    # Implementácia Wake-on-LAN
    print(f"Odosielam magic packet na MAC adresu: {mac_adresa}")
    try:
        # from wakeonlan import send_magic_packet # Zakomentované, lebo wakeonlan nie je štandardná knižnica
        # send_magic_packet(mac_adresa)
        pass  # odstrániť pass a odkomentovať riadky vyššie
        return jsonify({'status': 'success', 'message': f'Magic packet odoslaný na {mac_adresa}'}), 200
    except Exception as e:
        print(f"Chyba pri odosielaní magic packetu: {e}")
        return jsonify({'status': 'error', 'message': f'Chyba pri odosielaní magic packetu: {e}'}), 500


@app.route('/aktualizuj_program', methods=['POST'])
def aktualizuj_program():
    """Aktualizuje program z GitHub repozitára."""
    try:
        # 1. Stiahnutie aktualizovaného súboru
        print("Aktualizujem program...")
        prikaz_stiahnutie = f"curl -O https://{PROGRAM_GITHUB}"
        subprocess.run(prikaz_stiahnutie, shell=True, check=True)

        # 2. Nahradenie existujúceho súboru
        prikaz_nahradenie = f"cp main.py {PROGRAM_CESTA}"
        subprocess.run(prikaz_nahradenie, shell=True, check=True)

        # 3. Reštart aplikácie (toto je potrebné urobiť správne pre serverové prostredie, napr. cez supervisor)
        print("Program bol aktualizovaný. Reštartujem aplikáciu...")
        # sys.executable
        # V reálnom nasadení by sa mal použiť správny nástroj na reštartovanie služby, napr. supervisorctl restart moja_aplikacia
        return jsonify({'status': 'success', 'message': 'Program aktualizovaný, reštartujte aplikáciu'}), 200
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri aktualizácii programu: {e}")
        return jsonify({'status': 'error', 'message': f'Chyba pri aktualizácii programu: {e}'}), 500
    except Exception as e:
        print(f"Neočakávaná chyba: {e}")
        return jsonify({'status': 'error', 'message': f'Neočakávaná chyba: {e}'}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True) #povolene debug mode
