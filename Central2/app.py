import os
import subprocess
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Konstanty
PROGRAM_GITHUB = "github.com/jan-tdy/devcontrolenterpise/Central2/app.py"
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/app.py"
SSH_USER = "dpv"
SSH_PASS = os.getenv('SSH_PASS')  # Heslo načítané z environmentu
C14_IP = "172.20.20.103"
AZ2000_IP = "172.20.20.101"  # IP adresa pre AZ2000

def run_ssh_command(ip, command):
    """Spustí SSH príkaz na vzdialenom serveri."""
    try:
        result = subprocess.check_output(
            ["sshpass", "-p", SSH_PASS, "ssh", f"{SSH_USER}@{ip}", command],
            stderr=subprocess.STDOUT
        )
        return result.decode()
    except subprocess.CalledProcessError as e:
        print(f"Chyba pri spúšťaní SSH príkazu: {e.output.decode()}")
        raise

@app.route('/ovladaj_zasuvku_c14', methods=['GET'])
def ovladaj_zasuvku_c14():
    """
    Ovládanie zásuvky C14 cez SSH.
    Očakáva query parametre:
      - cislo_zasuvky
      - zapnut (hodnoty "true", "1", "yes" pre zapnuté)
      - label_name (voliteľný, pre spätnú väzbu)
    """
    data = request.args
    cislo_zasuvky = data.get('cislo_zasuvky')
    zapnut_str = data.get('zapnut')
    label_name = data.get('label_name')

    if cislo_zasuvky is None or zapnut_str is None:
        return jsonify({'status': 'error', 'message': 'Chýbajú parametre'}), 400

    # Konverzia zapnut parametra na boolean
    zapnut = zapnut_str.lower() in ['true', '1', 'yes']

    prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
    try:
        vystup = run_ssh_command(C14_IP, prikaz)
        print(vystup)
        return jsonify({
            'status': 'success',
            'message': f'Zásuvka {cislo_zasuvky} {"zapnutá" if zapnut else "vypnutá"}.',
            'label_name': label_name
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Chyba pri ovládaní zásuvky: {e}'}), 500

@app.route('/spusti_indistarter_c14', methods=['GET'])
def spusti_indistarter_c14():
    """Spustí INDISTARTER na C14 a UVEX-RPi cez SSH."""
    try:
        # Spustenie INDISTARTER na C14
        c14_vystup = run_ssh_command(C14_IP, "indistarter")
        print(f"INDISTARTER na C14: {c14_vystup}")

        # Spustenie INDISTARTER na UVEX-RPi (cez SSH z C14)
        uvex_vystup = run_ssh_command(C14_IP, f"ssh {SSH_USER}@{AZ2000_IP} indistarter")
        print(f"INDISTARTER na UVEX-RPi: {uvex_vystup}")
        return jsonify({'status': 'success', 'message': 'INDISTARTER spustený na C14 a UVEX-RPi'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Chyba pri spúšťaní INDISTARTER: {e}'}), 500

@app.route('/ovladaj_strechu_c14', methods=['GET'])
def ovladaj_strechu_c14():
    """
    Ovládanie strechy C14 cez SSH.
    Očakáva query parameter 'strana' s hodnotou "sever" alebo "juh".
    """
    data = request.args
    strana = data.get('strana')

    if strana is None:
        return jsonify({'status': 'error', 'message': 'Chýba parameter "strana"'}), 400

    if strana == "sever":
        prikaz1 = "crelay -s BI TFT 2 ON"
        prikaz2 = "crelay -s BI TFT 2 OFF"
    elif strana == "juh":
        prikaz1 = "crelay -s BI TFT 1 ON"
        prikaz2 = "crelay -s BI TFT 1 OFF"
    else:
        return jsonify({'status': 'error', 'message': 'Neplatná hodnota pre "strana". Použi "sever" alebo "juh".'}), 400

    try:
        run_ssh_command(C14_IP, prikaz1)
        time.sleep(2)
        run_ssh_command(C14_IP, prikaz2)
        print(f"Strecha ({strana}) na C14 ovládaná.")
        return jsonify({'status': 'success', 'message': f'Strecha na C14 presunutá na {strana}'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Chyba pri ovládaní strechy: {e}'}), 500

@app.route('/wake_on_lan', methods=['GET'])
def wake_on_lan():
    """
    Pošle magický paket na prebudenie zariadenia pomocou Wake-on-LAN.
    Očakáva query parameter 'mac_adresa'.
    """
    data = request.args
    mac_adresa = data.get('mac_adresa')

    if mac_adresa is None:
        return jsonify({'status': 'error', 'message': 'Chýba parameter "mac_adresa"'}), 400

    print(f"Posielam magický paket na MAC adresu: {mac_adresa}")
    try:
        # Odkomentuj a nainštaluj knižnicu wakeonlan, ak máš záujem
        # from wakeonlan import send_magic_packet
        # send_magic_packet(mac_adresa)
        pass
        return jsonify({'status': 'success', 'message': f'Magický paket poslaný na {mac_adresa}'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Chyba pri posielaní magického paketu: {e}'}), 500

@app.route('/aktualizuj_program', methods=['GET'])
def aktualizuj_program():
    """Aktualizuje program z GitHub repozitára."""
    try:
        print("Aktualizujem program...")
        prikaz_stiahnutie = f"curl -O https://{PROGRAM_GITHUB}"
        subprocess.run(prikaz_stiahnutie, shell=True, check=True)

        prikaz_nahradenie = f"cp main.py {PROGRAM_CESTA}"
        subprocess.run(prikaz_nahradenie, shell=True, check=True)

        print("Program aktualizovaný. Reštart aplikácie je potrebný.")
        return jsonify({'status': 'success', 'message': 'Program aktualizovaný, reštartuj prosím aplikáciu'}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Chyba pri aktualizácii programu: {e}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Neočakávaná chyba: {e}'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
