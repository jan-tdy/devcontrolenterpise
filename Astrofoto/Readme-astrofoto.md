> [!WARNING]
> **This program is no longer maintained.**
> For support or questions, contact [j44soft@gmail.com](mailto:j44soft@gmail.com).
> A newer, actively developed version is available at [devcontrol2.gitbook.io](https://devcontrol2.gitbook.io/devcontrol2).

# DevControl Enterprise Astrofoto

[![License][license-shield]](LICENSE)
[![Maintenance](https://img.shields.io/maintenance/no/2026?style=for-the-badge)](https://github.com/jan-tdy/devcontrolenterpise)
[![Stars][stars-shield]][stars]
[![Issues][issues-shield]][issues]
[![Discussions][discussions-shield]][discussions]

## About

What began as a simple script to manage a programmable power strip in an astronomical observatory has evolved into a comprehensive control suite. **DevControl Enterprise Astrofoto** provides power strip control, roof automation, and WOL support for the Astrofoto pavilion at Vihorlat Observatory.

> **Note:** This program targets **Raspbian Bullseye** and is no longer actively developed. Bug fixes may be applied but no new features are planned.

## Known Issues / Security Notes

- `SSH_PASS` and `SSH_PASS2` are hardcoded in the source. Do **not** distribute this binary or source publicly.
- OTA update downloads raw Python from GitHub and writes it directly to the running file with no signature verification. Only use on a trusted network.

## Community & Support

* **Bug Reports & Feature Requests:** Please post any issues [here][issues].
* **Community Chat:** Join the discussion [here][discussions].
* **Source Code:** Explore the repository [here](https://github.com/jan-tdy/devcontrolenterpise).

---

*Developed and maintained by **JapySoft***

[license-shield]: https://img.shields.io/github/license/jan-tdy/devcontrolenterpise?style=for-the-badge
[issues-shield]: https://img.shields.io/github/issues/jan-tdy/devcontrolenterpise?style=for-the-badge
[issues]: https://github.com/jan-tdy/devcontrolenterpise/issues
[discussions-shield]: https://img.shields.io/badge/GitHub-Discussions-blue?style=for-the-badge&logo=github
[discussions]: https://github.com/jan-tdy/devcontrolenterpise/discussions
[stars-shield]: https://img.shields.io/github/stars/jan-tdy/devcontrolenterpise?style=for-the-badge
[stars]: https://github.com/jan-tdy/devcontrolenterpise/stargazers
