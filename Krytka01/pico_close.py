#!/usr/bin/env python3
import os, sys, time
try:
    import serial, serial.tools.list_ports
except ModuleNotFoundError:
    print("Chýba pyserial. Nainštaluj: pip3 install pyserial", file=sys.stderr)
    sys.exit(2)

BAUD = 115200
VID = 0x2E8A
PIDS_PREFER = {0x0005}

def find_pico(cli_port: str | None):
    if cli_port:
        return cli_port
    env = os.environ.get("PICO_PORT")
    if env:
        return env
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if getattr(p, "vid", None) == VID and getattr(p, "pid", None) in PIDS_PREFER:
            return p.device
    for p in ports:
        descr = (p.description or "") + " " + (p.manufacturer or "")
        if any(key in descr for key in ("MicroPython", "Pico", "Raspberry Pi")) and p.device.startswith(("/dev/ttyACM", "/dev/ttyUSB", "COM")):
            return p.device
    raise RuntimeError("Nenašiel som Pico. Zadaj port: pico_close.py /dev/ttyACM1 alebo PICO_PORT.")

def main():
    cli_port = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] not in ("-h","--help") else None
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Použitie: pico_close.py [SERIAL_PORT]\nPr.: pico_close.py /dev/ttyACM1")
        sys.exit(0)
    try:
        port = find_pico(cli_port)
        with serial.Serial(port, BAUD, timeout=1) as ser:
            time.sleep(0.2)
            ser.reset_input_buffer()
            ser.write(b"CLOSE\r\n")
            ser.flush()
            time.sleep(0.05)
            resp = ser.readline().decode(errors="ignore").strip()
        print("OK" if not resp else resp)
    except Exception as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
