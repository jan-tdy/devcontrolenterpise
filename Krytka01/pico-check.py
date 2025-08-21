#!/usr/bin/env python3
import sys, time, serial, re
import serial.tools.list_ports

TARGET_MANUFACTURER = "Japysoft"
TARGET_PRODUCT = "Brain of Japysoft Telescope Cover"
TARGET_SERIAL = "japydevusb-082501"
BAUD = 115200

def find_pico():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if (p.manufacturer == TARGET_MANUFACTURER and
            p.product == TARGET_PRODUCT and
            p.serial_number == TARGET_SERIAL):
            return p.device
    return None

def main():
    port = find_pico()
    if not port:
        print("❌ Pico (Japysoft) nenašiel som!", file=sys.stderr)
        sys.exit(1)
    try:
        with serial.Serial(port, BAUD, timeout=1) as ser:
            ser.reset_input_buffer()
            ser.write(b"STATE\n")
            ser.flush()
            deadline = time.time() + 2.0
            buf = ""
            while time.time() < deadline:
                line = ser.readline().decode(errors="ignore")
                if not line:
                    continue
                buf += line
                m = re.search(r"\b([01])\b", buf)
                if m:
                    print(m.group(1), end="")
                    sys.exit(0)
        sys.exit(3)  # nič neprišlo
    except Exception as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
