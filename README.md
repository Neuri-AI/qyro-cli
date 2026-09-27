<p align="center">
  <img src="https://ik.imagekit.io/kummiktgaiq/ppg/Qyro-logo.svg?updatedAt=1755215983279" alt="Qyro Logo" width="50%">
</p>

# ⚡ Qyro CLI

> **The official developer CLI and project orchestrator for the [Qyro](https://github.com/Neuri-AI/qyro) desktop and mobile application ecosystem.**

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14%20%7C%203.15-blue.svg)](https://python.org)
![GitHub Release](https://img.shields.io/github/v/release/runesc/qyro-engine?include_prereleases&display_name=release&color=stable)
![GitHub Issues](https://img.shields.io/github/issues/runesc/qyro-engine?color=%23ab7df8)
![GitHub Issues Closed](https://img.shields.io/github/issues-closed/runesc/qyro-engine?color=green)
![GitHub forks](https://img.shields.io/github/forks/runesc/qyro-engine)
![GitHub stars](https://img.shields.io/github/stars/runesc/qyro-engine)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

- **⚡ Unified Multi-Framework Support:** Scaffold projects for **PySide6**, **PyQt6**, **PyQt5**, **PySide2**, **Kivy**, or **Tkinter**.
- **🔄 Smart Template Resolution:** Uses template providers with fallback support for robust initialization workflows.
- **❄️ Packaging & Freezing Ready:** Native freezing for desktop targets with PyInstaller.
- **📦 Distribution Bundling:** Platform-aware bundling for DMG, NSIS, and Linux package formats.
- **✅ Release Preflight Checks:** Validate dependencies and `release.json` paths/options before packaging.
- **🧹 Artifact Cleanup:** Clean build outputs and optional release outputs with one command.

---

## 🚀 Installation

### Core CLI

```bash
# Using pip
pip install qyro-cli

# Using Poetry
poetry add qyro-cli
```

### Desktop Packaging Support (PyInstaller)

```bash
# Using pip
pip install "qyro-cli[desktop]"

# Using Poetry
poetry add qyro-cli -E desktop
```

### Mobile Packaging Support (Buildozer)

```bash
# Using pip
pip install "qyro-cli[mobile]"

# Using Poetry
poetry add qyro-cli -E mobile
```

### Complete Bundle (Desktop + Mobile)

```bash
# Using pip
pip install "qyro-cli[all]"

# Using Poetry
poetry add qyro-cli -E all
```

---

## 💻 Quick Start & Usage

### 1) Initialize a project

```bash
qyro init --name my-app
```

You can preselect a binding and template version:

```bash
qyro init --name my-app --binding PySide6 --template-version 1.0.0
```

Supported `--binding` values:

- `PySide6`
- `PyQt6`
- `PyQt5`
- `PySide2`
- `Kivy`
- `Tkinter`

### 2) Run from source

```bash
cd my-app
qyro start
```

Note: `qyro start` currently runs from source without release flag variants.

### 3) Freeze executable artifacts

```bash
# default desktop target, profile=release
qyro build

# single executable
qyro build --onefile
# or
qyro build --mode onefile

# platform profile override
qyro build --target mac
qyro build --target windows
qyro build --target linux

# extra controls
qyro build --debug --console --uac --clean --interactive
```

### 4) Bundle for distribution

```bash
# auto format by host OS
qyro bundle

# explicit platform and format
qyro bundle --platform mac --format dmg
qyro bundle --platform windows --format nsis
qyro bundle --platform linux --format tar.gz
qyro bundle --platform linux --format deb
qyro bundle --platform linux --format rpm
qyro bundle --platform linux --format arch

# include an additional zip and custom output dir
qyro bundle --zip --release-dir release
```

### 5) Validate before packaging (preflight)

```bash
qyro bundle --check
```

This validates dependencies and `release` settings (like DMG background and extra files) without generating artifacts.

### 6) Clean outputs

```bash
# clean freeze directory (default: build/)
qyro clean

# also clean release/
qyro clean --release
```

---

## 🎛️ CLI Commands Reference

| Command | Flags / Args | Description |
| :--- | :--- | :--- |
| `qyro init` | `-n, --name` `-b, --binding` `--template-version` | Initialize a new project. |
| `qyro start` | none | Run the app from source. |
| `qyro create` | `component\|view <name>` `[--inherit <base>]` | Scaffold command entrypoint (currently minimal/placeholder implementation). |
| `qyro build` | `-m, --mode onedir|onefile` `--onefile` `--debug` `--console` `--uac` `-p, --profile` `-c, --clean` `-i, --interactive` `--target` `--init-spec` | Freeze/build artifacts. |
| `qyro bundle` | `--release-dir` `--no-resources` `--zip` `--platform` `--format` `--check` | Create distributable packages or run preflight checks. |
| `qyro clean` | `--release` | Remove generated build artifacts. |
| `qyro version` | none | Show current version info. |

---

## ⚙️ Bundle Configuration (`release.json`)

Projects can configure bundle behavior in:

- `build/settings/release.json` (legacy/generated layout)
- `settings/release.json` (also supported)

Example:

```json
{
  "release": true,
  "environment": "development",
  "bundle": {
    "dmg": {
      "window": { "x": 200, "y": 120 },
      "window_size": { "width": 660, "height": 420 },
      "icon_size": 120,
      "app_position": { "x": 180, "y": 180 },
      "applications_position": { "x": 480, "y": 180 },
      "background": "assets/dmg-background.jpg"
    },
    "extra_files": [
      "README.md",
      {
        "source": "docs/RELEASE_NOTES.md",
        "destination": "docs/RELEASE_NOTES.md"
      }
    ]
  }
}
```

### `bundle.extra_files`

Supports:

- String path: copied to bundle root.
- Object with `source` + `destination`: copied to relative destination inside bundle.

Validation rules:

- `source` must exist.
- `destination` must be relative (no absolute paths).
- `destination` cannot escape output directory.

### `bundle.dmg`

When DMG custom options are set, `create-dmg` is required.

If no DMG custom options are set, bundling can fallback to native `hdiutil`.

---

## 🧰 Packaging Dependencies

| Format | Requirement |
| :--- | :--- |
| `dmg` with customization | `create-dmg` |
| `dmg` without customization | `hdiutil` (macOS) |
| `nsis` | `makensis` |
| `deb`, `rpm`, `arch` | `fpm` |

Install `create-dmg` on macOS with one of:

```bash
brew install create-dmg
# or
npm install -g create-dmg
```

---

## 🖼️ Supported Framework Ecosystem

`qyro-cli` generates apps that integrate natively with `qyro-engine` adapters:

| Binding | Adapter | Best For |
| :--- | :--- | :--- |
| **PySide6** | `PySide6Adapter` | Modern Qt 6 desktop apps with rich widgets and tooling. |
| **PyQt6** | `PyQt6Adapter` | Feature-complete Qt 6 desktop software. |
| **PyQt5** | `PyQt5Adapter` | Legacy enterprise Qt 5 systems. |
| **PySide2** | `PySide2Adapter` | Official Qt 5 environments. |
| **Kivy** | `KivyAdapter` | Cross-platform touch interfaces for desktop/mobile. |
| **Tkinter** | `TkinterAdapter` | Zero-dependency desktop utilities built on stdlib. |

---

## 🔌 Built-in Add-ons

Projects can be configured with modular add-ons in settings:

- **`hotrl` (Hot Reloading):** Iterative development with live code reload.
- **`pydux` (Predictable State):** Redux-inspired state container patterns.
- **`sentry` (Telemetry):** Exception and crash reporting integration.

---

## 📝 Notes for Developers

- `qyro bundle --check` is the fastest way to validate release readiness in CI.
- `qyro clean --release` is useful before reproducible release builds.
- If a bundle step fails, use the exact error output; validations are strict by design to avoid silent bad packages.

---

## 🤝 Contributing

Contributions to `qyro-cli` and the Qyro ecosystem are welcome.

1. Fork the repository on GitHub.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Run test suites (`poetry run pytest`).
4. Commit your changes (`git commit -m 'feat: add amazing feature'`).
5. Push to your branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request.

---

## 📄 License

MIT. See [LICENSE](LICENSE).

---

## 👥 Organization & Maintainers

- **Organization:** [Neuri](https://github.com/Neuri-AI)
- **Lead Maintainer:** Luis Alfredo De Los Reyes ([luisalfredoreyes98@gmail.com](mailto:luisalfredoreyes98@gmail.com))
- **Ecosystem:** [Qyro Engine](https://github.com/Neuri-AI/qyro-engine) • [Qyro CLI](https://github.com/Neuri-AI/qyro-cli) • [Boilerplates](https://github.com/Neuri-AI)
