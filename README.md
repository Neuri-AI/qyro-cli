<p align="center">
  <img src="https://ik.imagekit.io/kummiktgaiq/ppg/Qyro-logo.svg?updatedAt=1755215983279" alt="Qyro Logo" width="50%">
</p>

# ⚡ Qyro CLI

> **The official developer CLI and project orchestrator for the [Qyro](https://github.com/Neuri-AI/qyro) desktop and mobile application ecosystem.**

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://python.org)
![GitHub Release](https://img.shields.io/github/v/release/runesc/qyro-engine?include_prereleases&display_name=release&color=stable)
![GitHub Issues](https://img.shields.io/github/issues/runesc/qyro-engine?color=%23ab7df8)
![GitHub Issues Closed](https://img.shields.io/github/issues-closed/runesc/qyro-engine?color=green)
![GitHub forks](https://img.shields.io/github/forks/runesc/qyro-engine)
![GitHub stars](https://img.shields.io/github/stars/runesc/qyro-engine)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

* **⚡ Unified Multi-Framework Support:** Scaffold projects for **PySide6**, **PyQt6**, **PyQt5**, **PySide2**, **Kivy**, or zero-dependency **Tkinter** with a single command.
* **🔄 Smart Template Resolution:** Fetches official SemVer-pinned templates directly from GitHub (`^1.0.0`), with persistent local caching and offline fallback providers.
* **🔥 Live Hot Reloading:** Instant dev-mode reloading via `hotrl` to iterate rapidly without restarting application processes.
* **📦 Smart Resource Resolver:** Pre-configures platform-aware asset directories (`resources/base/`, `resources/windows/`, `resources/mac/`, `resources/linux/`).
* **❄️ Packaging & Freezing Ready:** Automated native bundling with PyInstaller for **Windows** (`.exe`), **macOS** (`.app` with custom bundle IDs), and **Linux**, plus mobile scaffolding for **Android & iOS**.
* **🧩 Standardized Scaffolder:** Generates uniform, production-ready components and views.

---

## 🚀 Installation

### Core CLI
```bash
# Using pip
pip install qyro-cli

# Using Poetry
poetry add qyro-cli
```

### With Desktop Packaging (PyInstaller)
For building standalone `.exe`, `.app`, and Linux executables with `qyro build`:
```bash
# Using pip
pip install "qyro-cli[desktop]"

# Using Poetry
poetry add qyro-cli -E desktop
```

### With Mobile Packaging (Buildozer)
For packaging Android and iOS mobile bundles:
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

### 1. Initialize a Project

Run the interactive wizard:

```bash
qyro init -n my-awesome-app
```

Or pass flags directly for automated environments:

```bash
# Initialize a PySide6 project with hot reloading and state management
qyro init -n my-awesome-app --binding PySide6

# Initialize a lightweight, zero-dependency Tkinter app
qyro init -n my-utility --binding Tkinter
```

The wizard configures:
- **Application Metadata:** Name, version, author, and macOS/iOS bundle identifier.
- **UI Framework Binding:** Select your preferred toolkit.
- **Add-ons:** Instant Hot Reloading (`hotrl`), Redux state container (`pydux`), and crash reporting (`sentry`).

---

### 2. Run in Development Mode

```bash
cd my-awesome-app
qyro start
```

Starts your application in dev mode with live hot reloading enabled. To run in release mode:

```bash
qyro start --release
```

---

### 3. Scaffold Components & Views

```bash
# Scaffold a new reusable UI component in src/components/
qyro create component NavigationBar

# Scaffold a new top-level view in src/views/
qyro create view SettingsDashboard
```

---

### 4. Build and Freeze for Production

```bash
# Package into a clean release directory inside target/
qyro build

# Create a single standalone executable file (--onefile)
qyro build --bundle

# Debug build for troubleshooting
qyro build --debug
```

---

## 🎛️ CLI Commands Reference

| Command | Arguments & Flags | Description |
| :--- | :--- | :--- |
| `qyro init` | `[path]` `[-n <name>]` `[--binding <binding>]` | Interactive project setup wizard or flag-driven generator. |
| `qyro start` | `[--release]` | Boots the application in dev mode (hot reload) or production mode. |
| `qyro create component` | `<name>` | Scaffolds a new component file inside `src/components/`. |
| `qyro create view` | `<name>` | Scaffolds a new full-screen view inside `src/views/`. |
| `qyro build` | `[--debug]` `[--bundle]` | Compiles and freezes the application into native executables. |
| `qyro freeze` | `[--debug]` `[--bundle]` | Alias for `qyro build`. |
| `qyro clean` | — | Cleans `build/` directory and temporary build artifacts. |
| `qyro version` | — | Displays the current Qyro CLI and Qyro Engine versions. |

---

## 🖼️ Supported Framework Ecosystem

`qyro-cli` generates apps that integrate natively with `qyro-engine`'s framework adapters:

| Binding | Adapter | Best For |
| :--- | :--- | :--- |
| **PySide6** | `PySide6Adapter` | Modern, official Qt 6 applications with high-fidelity widgets and QML. |
| **PyQt6** | `PyQt6Adapter` | Feature-complete Qt 6 desktop software. |
| **PyQt5** | `PyQt5Adapter` | Legacy enterprise Qt 5 systems. |
| **PySide2** | `PySide2Adapter` | Official Qt 5 environments. |
| **Kivy** | `KivyAdapter` | Cross-platform touch and mobile interfaces (Android / iOS / Desktop). |
| **Tkinter** | `TkinterAdapter` | Zero-dependency, ultra-compact desktop utilities (built into Python standard library). |

---

## 🔌 Built-in Add-ons

Every project can be configured with modular add-ons maintained in `settings/base.json`:

- **`hotrl` (Hot Reloading):** Watches project files and hot-swaps component code in real time without dropping application state.
- **`pydux` (Predictable State):** Redux-inspired unidirectional store with dispatchers, actions, and UI subscriptions.
- **`sentry` (Telemetry):** Production-grade exception capture and performance monitoring.

---

## 🤝 Contributing

Contributions to `qyro-cli` and the Qyro ecosystem are welcome!

1. Fork the repository on GitHub.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Run test suites (`poetry run pytest`).
4. Commit your changes with clear messages (`git commit -m 'feat: add amazing feature'`).
5. Push to the branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 👥 Organization & Maintainers

- **Organization:** [Neuri](https://github.com/Neuri-AI)
- **Lead Maintainer:** Luis Alfredo De Los Reyes ([luisalfredoreyes98@gmail.com](mailto:luisalfredoreyes98@gmail.com))
- **Ecosystem:** [Qyro Engine](https://github.com/Neuri-AI/qyro-engine) • [Qyro CLI](https://github.com/Neuri-AI/qyro-cli) • [Boilerplates](https://github.com/Neuri-AI)
