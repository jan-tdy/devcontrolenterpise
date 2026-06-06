
# DevControl DSLR (Astro-Sequencer)

A PyQt6-based graphical user interface for controlling DSLR cameras (tested with Canon 6D) specifically designed for astrophotography. It utilizes `gphoto2` under the hood to manage connections over USB or WiFi (PTP/IP).

## Features
* **Astro-Themed UI:** Dark red interface designed to preserve night vision during observation sessions.
* **Dual Connection Modes:** Supports reliable USB tethering and wireless PTP/IP (WiFi) connections.
* **Advanced Sequencer:** Automate your imaging sessions with precise control over frame counts and intervals.
* **Dynamic File Naming:** Custom pattern builder for easy file organization (e.g., Object, Frame Type, ISO, Exposure, Timestamp).
* **Astro-Specific Controls:** Direct toggles for Mirror Lockup (MLU), LCD screen power management (to reduce thermal noise), and manual focus stepping.
* **OTA Updates:** Built-in update checker that pulls the latest stable script version directly from this repository.

## Prerequisites

This application acts as a wrapper around `gphoto2`. You **must** have the `gphoto2` command-line utility installed on your operating system.

**Linux (Debian/Ubuntu/Raspberry Pi OS):**
```bash
sudo apt update
sudo apt install gphoto2

```
**Python Dependencies:**
The script requires Python 3 and a few external libraries. Install them via pip:
```bash
pip3 install PyQt6 requests

```
## Usage
Run the script from your terminal:
```bash
python3 devcontrol_dslr.py

```
### File Naming Pattern Guide
You can customize how your RAW files are saved using the following wildcards:
 * %O - Target Object Name
 * %T - Frame Type (Light, Dark, Flat, Bias)
 * %N - Sequence Number (e.g., 001, 002)
 * %I - ISO Value
 * %E - Exposure Time (automatically replaces / with - for OS compatibility)
 * %D - Current Date (YYYYMMDD)
 * %H - Current Time (HHMMSS)
### Troubleshooting WiFi (PTP/IP)
If you encounter a *'PTP Device Busy'* error while using the WiFi connection, try increasing the interval (pause) between frames in the sequencer settings to give the camera's network buffer more time to clear.
