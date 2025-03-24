from flask import Flask, request, jsonify
import paramiko
import socket

app = Flask(__name__)

C14_IP = "172.20.20.103"
SSH_USER = "dpv"
SSH_PASS = "otj0711"
SSH_PORT = 2222


def execute_ssh_command(command):
    """Vykoná SSH príkaz na C14 a vráti výsledok."""
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(C14_IP, port=SSH_PORT, username=SSH_USER,
                         password=SSH_PASS, timeout=10)

        stdin, stdout, stderr = ssh_client.exec_command(command)
        vystup = stdout.read().decode().strip()
        chyby = stderr.read().decode().strip()

        ssh_client.close()

        if chyby:
            return {"error": chyby}
        return {"output": vystup}

    except paramiko.AuthenticationException:
        return {"error": "Chyba autentifikácie"}
    except paramiko.SSHException as e:
        return {"error": f"Chyba SSH: {e}"}
    except socket.timeout:
        return {"error": "Časový limit prekročený"}
    except Exception as e:
        return {"error": f"Chyba: {e}"}


@app.route('/ssh', methods=['POST'])
def ssh_endpoint():
    """Endpoint pre prijímanie SSH príkazov z webového rozhrania."""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Chýba príkaz'}), 400

    command = data['command']
    vysledok = execute_ssh_command(command)
    return jsonify(vysledok), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # Spustíme server pre Flask
