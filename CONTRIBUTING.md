# Contributing to DevControl Enterprise

Thank you for your interest in contributing!

## Active Projects

Contributions are welcome for:

- **Krytka01** — Telescope cover controller (PyQt5 + Raspberry Pi Pico + MicroPython)
- **DSLR\_supported** — Astrophotography sequencer (PyQt6 + gphoto2)

The **Astrofoto** and **C14** directories are unmaintained. Bug reports are accepted but no new features are planned.

## Getting Started

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/my-fix`
3. Make your changes and test them locally
4. Push to your fork: `git push origin feature/my-fix`
5. Open a Pull Request against the `main` branch

## Code Style

- Follow PEP 8 (4-space indent, ~100 chars per line)
- Use `Path` over string paths
- Add type hints where practical
- **PyQt rule:** never call GUI methods from a non-main thread — use signals/slots for all cross-thread communication
- Keep comments minimal; prefer self-documenting names

## Testing

```bash
# Krytka01
cd Krytka01
pip install -r requirements.txt
python devcontrol.py

# DSLR_supported
cd DSLR_supported
pip install -r requirements.txt
# also requires: sudo apt install gphoto2
python devcontrol_dslr.py
```

## Reporting Bugs

Open an [issue](https://github.com/jan-tdy/devcontrolenterpise/issues) with:

- Which program (Krytka01 / DSLR\_supported / Astrofoto / C14)
- OS and Python version
- Steps to reproduce
- Expected vs actual behaviour

## Contact

For custom observatory control solutions or questions: [j44soft@gmail.com](mailto:j44soft@gmail.com)
