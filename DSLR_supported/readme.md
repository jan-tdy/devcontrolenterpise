# DevControl DSLR – Astrophotography Sequencer

[![License][license-shield]](../LICENSE)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4%2B-green?style=for-the-badge)
![gphoto2](https://img.shields.io/badge/gphoto2-required-orange?style=for-the-badge)

A PyQt6 GUI for controlling DSLR cameras (tested with **Canon 6D**) during deep-sky astrophotography sessions. Wraps `gphoto2` to manage connections over **USB** or **WiFi (PTP/IP)**. Designed for observatory use with a red night-vision-safe dark theme.

> **Contact / custom builds:** j44soft@gmail.com

---

## Features

| Feature | Description |
|---|---|
| **Astro dark theme** | Deep red/black UI to preserve night vision |
| **USB & WiFi** | USB tethering or PTP/IP wireless (Canon 6D WiFi) |
| **Imaging sequencer** | Multi-frame sessions with configurable frame count and interval |
| **Dynamic file naming** | Pattern system with object, frame type, ISO, exposure, date/time wildcards |
| **Astro controls** | Mirror Lockup, LCD disable (reduces sensor heat), manual focus stepping |
| **Non-blocking settings** | ISO/shutter applied in a background thread – UI stays responsive |
| **OTA updates** | Background version check and in-app update from GitHub |

---

## Architecture

```
devcontrol_dslr.py
 ├── UpdateWorker(QThread)        – background GitHub version check
 ├── ApplySettingsWorker(QThread) – ISO/shutter/MLU/LCD off main thread
 └── GphotoWorker(QThread)        – imaging sequence / single command
         └── subprocess gphoto2        – USB or PTP/IP camera control
```

---

## Prerequisites

### gphoto2

**Linux (Debian/Ubuntu/Raspberry Pi OS):**
```bash
sudo apt update && sudo apt install gphoto2
```

**macOS:**
```bash
brew install gphoto2
```

### Python dependencies

```bash
pip3 install -r requirements.txt
# or
pip3 install "PyQt6>=6.4" "requests>=2.28"
```

---

## Usage

```bash
python3 devcontrol_dslr.py
```

### Connection

1. Select **USB** (default) or **WiFi** and enter the camera IP (Canon 6D default: `192.168.5.204`).
2. Click **Test Connection** – runs `gphoto2 --auto-detect` and shows output in the log.

### File Naming Patterns

| Wildcard | Meaning | Example output |
|---|---|---|
| `%O` | Target object name | `M42` |
| `%T` | Frame type | `Light` / `Dark` / `Flat` / `Bias` |
| `%N` | Sequence number (3-digit zero-padded) | `001` |
| `%I` | ISO value | `1600` |
| `%E` | Exposure time (`/` replaced by `-`) | `300` or `1-100` |
| `%D` | Date | `20260610` |
| `%H` | Time | `210530` |

Default pattern: `%O_%T_S%N_ISO%I_%E`
Example output: `M42_Light_S001_ISO1600_300.CR2`

### Imaging Sequence

1. Set **Object** name and file-naming **Pattern**.
2. Select **Type**, **ISO**, and **Exposure**. For exposures > 30 s use **bulb** and set duration.
3. Set **Frames** count and **Interval** (seconds between frames).
4. Click **START**. Use **STOP** to abort.

### Applying Camera Settings

**Apply ISO / Shutter** pushes ISO, shutter speed, Mirror Lockup, and LCD state to the camera. Commands run in a background thread so the UI stays fully responsive.

---

## Known Limitations

- Files are always saved as `.CR2` (Canon RAW). For other cameras adjust the `--filename` extension in `GphotoWorker.run()`.
- Bulb accuracy depends on OS timer precision — avoid very short bulb values.
- WiFi connections are sensitive to latency. Increase interval if you see **PTP Device Busy** errors.
- OTA writes the new script directly to `__file__` without hash verification. Only accept updates from your own trusted repository.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `gphoto2` not found | Not installed | `sudo apt install gphoto2` |
| PTP Device Busy (WiFi) | Camera buffer full | Increase interval between frames (≥10 s) |
| UI freezes on Apply Settings | Old version bug | Fixed in current version (worker thread) |
| Files saved in wrong location | Filename is relative to cwd | Run from your target directory |

---

## License

MIT – see [../LICENSE](../LICENSE).
Contact: **j44soft@gmail.com**

[license-shield]: https://img.shields.io/github/license/jan-tdy/devcontrolenterpise?style=for-the-badge
