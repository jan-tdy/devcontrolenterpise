# Jadiv DEVCONTROL – Motorised Telescope Cover Controller

[![License][license-shield]](../LICENSE)
![Maintenance](https://img.shields.io/maintenance/yes/2026?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green?style=for-the-badge)

A PyQt5 desktop GUI for controlling a **motorised dome cover** at an astronomical observatory. The cover is driven by a servo motor connected to a **Raspberry Pi Pico** running MicroPython firmware (`main.py`). The desktop application communicates with the Pico over USB serial.

> **Contact / custom builds:** j44soft@gmail.com

---

## System Architecture

```
┌───────────────────────────────────────────┐
│          Desktop Computer             │
│                                        │
│  devcontrol.py  (PyQt5 GUI)            │
│   ├─ pico_open.py   ──sends OPEN\r\n  │
│   ├─ pico_close.py  ──sends CLOSE\r\n │
│   └─ pico-check.py  ──sends STATE\r\n │
│             │  USB serial 115200 baud  │
└─────────────┼────────────────────────┘
              │
┌─────────────▼────────────────────────┐
│    Raspberry Pi Pico (MicroPython)    │
│                                        │
│  main.py firmware                      │
│   ├─ servo on GPIO15 (PWM 50 Hz)      │
│   ├─ onboard LED heartbeat            │
│   └─ USB CDC command protocol         │
└─────────────────────────────────────────┘
              │
         Servo motor → cover mechanism
```

---

## Files

| File | Description |
|---|---|
| `devcontrol.py` | Desktop GUI application (PyQt5). Run on the control PC. |
| `main.py` | MicroPython firmware. Flash onto the Raspberry Pi Pico. |
| `pico_open.py` | CLI helper – sends `OPEN` command over serial. |
| `pico_close.py` | CLI helper – sends `CLOSE` command over serial. |
| `pico-check.py` | CLI helper – queries cover state (outputs `0` or `1`). |
| `led_def.png` | Grey LED icon (unknown state). |
| `led_green.png` | Green LED icon (cover open). |
| `led_red.png` | Red LED icon (cover closed). |
| `logo.png` | Application logo / window icon. |

---

## Prerequisites

### Desktop (runs `devcontrol.py`)

```bash
pip3 install -r requirements.txt
```

Dependencies: `PyQt5>=5.15`, `pyserial>=3.5`, `requests>=2.28`

### Pico (runs `main.py`)

Flash using [Thonny](https://thonny.org/) or `mpremote`. The firmware requires only the MicroPython standard library — no extra packages needed.

---

## Installation

### 1. Flash the Pico firmware

1. Hold **BOOTSEL** and plug the Pico in via USB.
2. Open Thonny → set interpreter to **MicroPython (Raspberry Pi Pico)**.
3. Open `main.py` and save it to the Pico.

### 2. Place CLI helpers on the desktop machine

The GUI expects the helper scripts in your **home directory**:

```bash
cp pico_open.py pico_close.py pico-check.py ~/
```

Or set a custom location with the environment variable:
```bash
export PICO_PORT=/dev/ttyACM1
```

### 3. Run the GUI

```bash
python3 devcontrol.py
```

The app auto-detects the Pico via USB VID/PID `0x2E8A`. Override with:
```bash
PICO_PORT=/dev/ttyACM1 python3 pico_open.py
```

---

## GUI Features

| Feature | Description |
|---|---|
| **Open / Close buttons** | Trigger cover movement. Button for current state is auto-disabled. |
| **LED status icon** | Green = open, red = closed, grey = unknown. Auto-refreshes every 3 s. |
| **Coloured status bar** | Bottom bar shows cover state with green/red/grey background. |
| **Activity log** | Colour-coded (green = success, red = error, grey = info). Saved to `~/pico_gui.log`. |
| **Scheduler** | Schedule automatic open/close at a specific date and time. |
| **OTA updates** | Help → Check for Updates – pulls latest version from GitHub and restarts. |
| **About dialog** | Help → About shows version and contact info. |

---

## Pico Serial Protocol

The `main.py` firmware speaks a line-based text protocol at **115200 baud**:

| Command | Response | Description |
|---|---|---|
| `OPEN` | `OK` | Move servo to open position |
| `CLOSE` | `OK` | Move servo to closed position |
| `STATE` | `0` or `1` | Query current state (0=closed, 1=open) |
| `PING` | `PONG` | Connectivity test |
| `GET_US` | `US_CLOSE=N US_OPEN=M` | Read servo calibration |
| `SET_US <min> <max> [SAVE]` | `OK SET_US …` | Set servo limits; optionally save to flash |
| `JOG +N` / `JOG -N` | `OK JOG …` | Fine-tune current servo position |
| `MOVE_US <us>` | `OK MOVE_US …` | Move to exact microsecond value |
| `ADMINCHECK` | multi-line | Diagnostic dump (version, servo, CPU, unique ID) |
| `SAVE` / `LOAD` | `OK SAVED` / `OK LOADED …` | Persist / reload calibration from flash |

---

## Hardware Wiring

```
Pico GPIO 15  ──► Servo signal wire (orange/yellow)
Pico VBUS     ──► Servo power (red)    [use external 5V for high-torque servos]
Pico GND      ──► Servo GND (brown/black)
```

Default calibration in firmware:
- `US_CLOSE = 1100 µs`
- `US_OPEN  = 1900 µs`

Adjust with `SET_US <min> <max> SAVE` to persist to Pico flash.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No Pico found | USB not connected or wrong driver | Check `lsusb`; set `PICO_PORT` env var |
| State always UNKNOWN | `pico-check.py` missing from `~/` | Copy helper to home directory |
| Servo doesn’t reach end stops | Calibration wrong | Use `JOG +N` / `-N`, then `SAVE` |
| Toast disappears instantly | Old version GC bug | Fixed in v2026.6_1.0+ |
| Progress bar frozen at splash | Old version overflow bug | Fixed in v2026.6_1.0+ |

---

## License

MIT – see [../LICENSE](../LICENSE).
Contact: **j44soft@gmail.com**

[license-shield]: https://img.shields.io/github/license/jan-tdy/devcontrolenterpise?style=for-the-badge
