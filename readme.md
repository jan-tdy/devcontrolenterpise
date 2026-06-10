# DevControl Enterprise

[![License][license-shield]](LICENSE)
![Maintenance](https://img.shields.io/badge/maintenance-Partially--active-green?style=for-the-badge)
[![Issues][issues-shield]][issues]
[![Stars][stars-shield]][stars]
[![Discussions][discussions-shield]][discussions]

Comprehensive observatory control suite for managing hardware at astronomical facilities. Originally developed for Vihorlat Observatory, now expanded to support multiple pavilion setups.

---

## Projects

| Program | Status | Platform | Description |
|---|---|---|---|
| [Krytka01](./Krytka01/) | ✅ **Active** | PyQt5 + Raspberry Pi Pico | Automated telescope cover (servo-driven lid) |
| [DSLR\_supported](./DSLR_supported/) | ✅ **Active** | PyQt6 + gphoto2 | DSLR astrophotography sequencer (Canon 6D) |
| [Astrofoto](./Astrofoto/) | ⚠️ **Unmaintained** | PyQt5, Raspbian Bullseye | Observatory power & roof control (legacy) |
| [C14](./C14/) | ⚠️ **Unmaintained** | PyQt5, Ubuntu 24.04 | Atacama pavilion power, roof & camera control (legacy) |

> **Astrofoto** and **C14** are no longer actively developed. For continued support see [devcontrol2.gitbook.io](https://devcontrol2.gitbook.io/devcontrol2) or contact [j44soft@gmail.com](mailto:j44soft@gmail.com).

---

## Quick Start

### Krytka01 — Telescope Cover Controller

```bash
cd Krytka01
pip install -r requirements.txt
python devcontrol.py
```

Hardware: Raspberry Pi Pico + servo motor + USB. See [Krytka01/readme.md](./Krytka01/readme.md) for full wiring, protocol docs, and troubleshooting.

### DSLR\_supported — Astrophotography Sequencer

```bash
cd DSLR_supported
pip install -r requirements.txt
# Install gphoto2: sudo apt install gphoto2
python devcontrol_dslr.py
```

Requires: Canon 6D (or compatible), gphoto2 CLI, PyQt6. See [DSLR\_supported/readme.md](./DSLR_supported/readme.md) for full setup.

---

## Repository Structure

```
devcontrolenterpise/
├── Krytka01/                  # Active — telescope cover controller
│   ├── devcontrol.py          # Main PyQt5 GUI
│   ├── main.py                # MicroPython firmware (Raspberry Pi Pico)
│   ├── pico_open.py           # CLI: send OPEN command via serial
│   ├── pico_close.py          # CLI: send CLOSE command via serial
│   ├── pico-check.py          # CLI: query cover state via serial
│   ├── requirements.txt
│   └── readme.md
├── DSLR_supported/            # Active — DSLR sequencer
│   ├── devcontrol_dslr.py     # Main PyQt6 GUI
│   ├── requirements.txt
│   └── readme.md
├── Astrofoto/                 # ⚠️ Unmaintained
│   ├── Astrofoto.py
│   └── Readme-astrofoto.md
├── C14/                       # ⚠️ Unmaintained (Atacama)
│   ├── C14.py
│   └── Readme-c14.md
├── CONTRIBUTING.md
└── readme.md
```

---

## About

What began as a simple script to control a programmable power strip in an astronomical observatory has evolved into a comprehensive control suite. **DevControl Enterprise** provides hardware management software for telescope pavilions and observatory facilities.

### History

- **v1**: Single-script power strip controller for Vihorlat Observatory
- **v2**: Expanded to multi-pavilion setup (Astrofoto + C14/Atacama)
- **Current**: Krytka01 (telescope cover) + DSLR\_supported (astrophotography sequencer); legacy modules archived
- **Future**: Krytka01 and DSLR\_supported will each move to their own dedicated repositories

---

## Community & Support

- **Bug Reports & Feature Requests:** [GitHub Issues][issues]
- **Community Chat:** [GitHub Discussions][discussions]
- **Custom Solutions:** Need DevControl for your own observatory? Contact [j44soft@gmail.com](mailto:j44soft@gmail.com)
- **New DevControl2:** [devcontrol2.gitbook.io](https://devcontrol2.gitbook.io/devcontrol2)

---

*Developed and maintained by **JapySoft TDY***

[license-shield]: https://img.shields.io/github/license/jan-tdy/devcontrolenterpise?style=for-the-badge
[issues-shield]: https://img.shields.io/github/issues/jan-tdy/devcontrolenterpise?style=for-the-badge
[issues]: https://github.com/jan-tdy/devcontrolenterpise/issues
[discussions-shield]: https://img.shields.io/badge/GitHub-Discussions-blue?style=for-the-badge&logo=github
[discussions]: https://github.com/jan-tdy/devcontrolenterpise/discussions
[stars-shield]: https://img.shields.io/github/stars/jan-tdy/devcontrolenterpise?style=for-the-badge
[stars]: https://github.com/jan-tdy/devcontrolenterpise/stargazers
[releases-shield]: https://img.shields.io/github/v/release/jan-tdy/devcontrolenterpise?style=for-the-badge
[releases]: https://github.com/jan-tdy/devcontrolenterpise/releases
