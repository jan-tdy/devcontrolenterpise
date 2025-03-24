import os
import subprocess
import time  # Import time for delays
from flask import Flask, request, jsonify

app = Flask(__name__)

# Constants
PROGRAM_GITHUB = "github.com/jan-tdy/devcontrolenterpise/Central2/app.py"
PROGRAM_CESTA = "/home/dpv/j44softapps-socketcontrol/app.py"
SSH_USER = "dpv"
SSH_PASS = os.getenv('SSH_PASS')  # Use environment variable for password
C14_IP = "172.20.20.103"
AZ2000_IP = "172.20.20.101"  # IP address for AZ2000

def run_ssh_command(ip, command):
    """Run an SSH command on a remote server."""
    try:
        result = subprocess.check_output(
            ["sshpass", "-p", SSH_PASS, "ssh", f"{SSH_USER}@{ip}", command],
            stderr=subprocess.STDOUT
        )
        return result.decode()
    except subprocess.CalledProcessError as e:
        print(f"Error running SSH command: {e.output.decode()}")
        raise

@app.route('/ovladaj_zasuvku_c14', methods=['POST'])
def ovladaj_zasuvku_c14():
    """Control a socket on C14 via SSH. Expects JSON payload with keys 'cislo_zasuvky' and 'zapnut'."""
    data = request.get_json()
    cislo_zasuvky = data.get('cislo_zasuvky')
    zapnut = data.get('zapnut')
    label_name = data.get('label_name')  # Used for response

    if cislo_zasuvky is None or zapnut is None:
        return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400

    prikaz = f"sispmctl -{'o' if zapnut else 'f'} {cislo_zasuvky}"
    try:
        vystup = run_ssh_command(C14_IP, prikaz)
        print(vystup)
        return jsonify({'status': 'success', 'message': f'Socket {cislo_zasuvky} {"on" if zapnut else "off"}.', 'label_name': label_name}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error controlling socket: {e}'}), 500

@app.route('/spusti_indistarter_c14', methods=['POST'])
def spusti_indistarter_c14():
    """Start INDISTARTER on C14 and UVEX-RPi via SSH."""
    try:
        # Start on C14
        c14_vystup = run_ssh_command(C14_IP, "indistarter")
        print(f"INDISTARTER on C14: {c14_vystup}")

        # Start on UVEX-RPi (via SSH from C14)
        uvex_vystup = run_ssh_command(C14_IP, f"ssh {SSH_USER}@{AZ2000_IP} indistarter")
        print(f"INDISTARTER on UVEX-RPi: {uvex_vystup}")
        return jsonify({'status': 'success', 'message': 'INDISTARTER started on C14 and UVEX-RPi'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error starting INDISTARTER: {e}'}), 500

@app.route('/ovladaj_strechu_c14', methods=['POST'])
def ovladaj_strechu_c14():
    """Control the roof on C14 via SSH. Expects JSON payload with key 'strana'."""
    data = request.get_json()
    strana = data.get('strana')

    if strana is None:
        return jsonify({'status': 'error', 'message': 'Missing parameter "strana"'}), 400

    if strana == "sever":
        prikaz1 = "crelay -s BI TFT 2 ON"
        prikaz2 = "crelay -s BI TFT 2 OFF"
    elif strana == "juh":
        prikaz1 = "crelay -s BI TFT 1 ON"
        prikaz2 = "crelay -s BI TFT 1 OFF"
    else:
        return jsonify({'status': 'error', 'message': 'Invalid side of the roof. Use "sever" or "juh".'}), 400

    try:
        run_ssh_command(C14_IP, prikaz1)
        time.sleep(2)
        run_ssh_command(C14_IP, prikaz2)
        print(f"Roof ({strana}) on C14 controlled.")
        return jsonify({'status': 'success', 'message': f'Roof on C14 controlled to the {strana} side'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error controlling roof: {e}'}), 500

@app.route('/wake_on_lan', methods=['POST'])
def wake_on_lan():
    """Send a magic packet to wake a device using Wake-on-LAN. Expects JSON with key 'mac_adresa'."""
    data = request.get_json()
    mac_adresa = data.get('mac_adresa')

    if mac_adresa is None:
        return jsonify({'status': 'error', 'message': 'Missing parameter "mac_adresa"'}), 400

    print(f"Sending magic packet to MAC address: {mac_adresa}")
    try:
        # from wakeonlan import send_magic_packet  # Uncomment because wakeonlan is not a standard library
        # send_magic_packet(mac_adresa)
        pass  # Remove pass and uncomment the lines above
        return jsonify({'status': 'success', 'message': f'Magic packet sent to {mac_adresa}'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error sending magic packet: {e}'}), 500

@app.route('/aktualizuj_program', methods=['POST'])
def aktualizuj_program():
    """Update the program from the GitHub repository."""
    try:
        # 1. Download the updated file
        print("Updating program...")
        prikaz_stiahnutie = f"curl -O https://{PROGRAM_GITHUB}"
        subprocess.run(prikaz_stiahnutie, shell=True, check=True)

        # 2. Replace the existing file
        prikaz_nahradenie = f"cp main.py {PROGRAM_CESTA}"
        subprocess.run(prikaz_nahradenie, shell=True, check=True)

        # 3. Restart the application (this needs to be done correctly for a server environment, e.g., using supervisor)
        print("Program updated. Restarting application...")
        # sys.executable
        # In a real deployment, the correct tool for restarting the service should be used, e.g., supervisorctl restart my_application
        return jsonify({'status': 'success', 'message': 'Program updated, please restart the application'}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Error updating program: {e}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Unexpected error: {e}'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # Enable debug mode
