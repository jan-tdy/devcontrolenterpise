#!/usr/bin/env python3
import os, sys, time
try:
    import serial, serial.tools.list_ports
except ModuleNotFoundError:
    print("Chýba pyserial. Nainštaluj: pip3 install pyserial", file=sys.stderr)
    sys.exit(2)

BAUD = 115200
VID = 0x2E8A  # Raspberry Pi
PIDS_PREFER = {0x0005}  # MicroPython FS mode na Pico (bežné)

def find_pico(cli_port: str | None):
    # 1) ak je zadaný port
    if cli_port:
        return cli_port
    # 2) env premenná
    env = os.environ.get("PICO_PORT")
    if env:
        return env
    # 3) autodetekcia
    ports = list(serial.tools.list_ports.comports())
    # najprv striktne VID/PID
    for p in ports:
        if getattr(p, "vid", None) == VID and getattr(p, "pid", None) in PIDS_PREFER:
            return p.device
    # potom podľa popisu/manufacturera
    for p in ports:
        descr = (p.description or "") + " " + (p.manufacturer or "")
        if any(key in descr for key in ("MicroPython", "Pico", "Raspberry Pi")) and p.device.startswith(("/dev/ttyACM", "/dev/ttyUSB", "COM")):
            return p.device
    raise RuntimeError("Nenašiel som Pico. Zadaj port: pico_open.py /dev/ttyACM1 alebo nastav PICO_PORT.")

def main():
    cli_port = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] not in ("-h","--help") else None
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Použitie: pico_open.py [SERIAL_PORT]\nPr.: pico_open.py /dev/ttyACM1")
        sys.exit(0)
    try:
        port = find_pico(cli_port)
        with serial.Serial(port, BAUD, timeout=1) as ser:
            time.sleep(0.2)  # nech sa CDC „preberie“
            ser.reset_input_buffer()
            ser.write(b"OPEN\r\n")
            ser.flush()
            time.sleep(0.05)
            resp = ser.readline().decode(errors="ignore").strip()
        print("OK" if not resp else resp)
    except Exception as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
