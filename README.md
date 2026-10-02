<p align="center">
  <img src="https://ik.imagekit.io/kummiktgaiq/ppg/Qyro-logo.svg?updatedAt=1755215983279" alt="Qyro Logo" width="50%">
</p>

# ⚡ Qyro CLI

> [!WARNING]
> **Mobile support is a work in progress.** Every mobile-related feature described in this document (Buildozer packaging, the `[mobile]` extra, Android/iOS targets, Kivy on mobile) is **not finished yet**. For now, Qyro CLI **only works for desktop** (Windows, macOS and Linux).
> 

> **The official developer CLI and project orchestrator for the [Qyro](https://github.com/Neuri-AI/qyro) desktop and mobile application ecosystem.**

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14%20%7C%203.15-blue.svg)](https://python.org)
![GitHub Release](https://img.shields.io/github/v/release/runesc/qyro?include_prereleases&display_name=release&color=stable)
![GitHub Issues](https://img.shields.io/github/isxsues/runesc/qyro?color=%23ab7df8)
![GitHub Issues Closed](https://img.shields.io/github/issues-closed/runesc/qyro?color=green)
![GitHub forks](https://img.shields.io/github/forks/runesc/qyro)
![GitHub stars](https://img.shields.io/github/stars/runesc/qyro)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Sponsor](https://img.shields.io/badge/Sponsor-Buy%20Me%20a%20Coffee-FFDD00?logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/neuri)


---

## ✨ Features

- **⚡ Unified Multi-Framework Support:** Scaffold projects for **PySide6**, **PyQt6**, **PyQt5**, **PySide2**, **Kivy**, or **Tkinter**.
- **🔄 Smart Template Resolution:** Uses template providers with fallback support for robust initialization workflows.
- **❄️ Packaging & Freezing Ready:** Native freezing for desktop targets with PyInstaller.
- **📦 Distribution Bundling:** Platform-aware bundling for DMG, NSIS, and Linux package formats.
- **🔐 Code Signing & Notarization:** Windows Authenticode and macOS signing with optional notarization/stapling.
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
> [!WARNING]
> **Mobile packaging is not ready yet.** The `[mobile]` extra and Buildozer integration are under active development and may be incomplete or change without notice. Please use the desktop workflow for now.
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
qyro init --name my-app --binding PySide6 --template-version 1.0.x
```

Supported `--binding` values:

- `PySide6`
- `PyQt6`
- `PyQt5`
- `PySide2`
- `Kivy`
- `Tkinter`
  
> [!NOTE]
> **Kivy** projects currently work on desktop only. Mobile builds (Android/iOS) are not supported yet.

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
> [!NOTE]
> Available `--target` values are desktop platforms only (`mac`, `windows`, `linux`). Mobile targets are not available yet.

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

### Validate before packaging (preflight)

```bash
qyro bundle --check
```

This validates dependencies and `release` settings (like DMG background and extra files) without generating artifacts.

### Windows NSIS customization (`settings/release.json`)

When packaging with `qyro bundle --platform windows --format nsis`, you can customize installer behavior using `bundle.nsis` in `settings/release.json`.

Supported options:

- `bundle.nsis.icons.install`: Path to installer icon (`.ico`).
- `bundle.nsis.icons.uninstall`: Path to uninstaller icon (`.ico`).
- `bundle.nsis.welcome_bitmap`: Path to welcome/finish bitmap image used by NSIS Modern UI.
- `bundle.nsis.install_location`: Base install location. Allowed values: `programfiles64` -> `$PROGRAMFILES64`, `programfiles32` -> `$PROGRAMFILES32`, `appdata` -> `$LOCALAPPDATA`.
- `bundle.nsis.execution_level`: Installer privilege level. Allowed values: `highest`, `admin`, `user`.

Defaults:

- `install_location`: `programfiles64`
- `execution_level`: `highest`
- `icons.install`: `resources/base/icons/install.ico` (used if file exists)
- `icons.uninstall`: `resources/base/icons/uninstall.ico` (used if file exists)
- `welcome_bitmap`: not set by default

Example:

```json
{
  "bundle": {
    "nsis": {
      "icons": {
        "install": "resources/base/icons/install.ico",
        "uninstall": "resources/base/icons/uninstall.ico"
      },
      "welcome_bitmap": "resources/base/welcome.bmp",
      "install_location": "programfiles64",
      "execution_level": "highest"
    }
  }
}
```

Tip:

- Run `qyro bundle --check --platform windows --format nsis` to validate NSIS option values and file paths before generating artifacts.

### Clean outputs

```bash
# clean freeze directory (default: build/)
qyro clean

# also clean release/
qyro clean --release
```

### Sign compiled artifacts

```bash
# preflight validation only
qyro sign --check --platform windows
qyro sign --check --platform mac

# sign frozen binaries/app bundle
qyro sign --platform windows
qyro sign --platform mac

# macOS notarization flow (sign + notarize + staple)
qyro sign --platform mac --notarize --staple --keychain-profile "QYRO-NOTARY"

# skip Gatekeeper assessment if desired
qyro sign --platform mac --notarize --staple --no-assess
```

### Signing guide (Windows + macOS)

Use `settings/release.json` (or `build/settings/release.json`) to configure signing.

#### Windows signing (Authenticode)

Requirements:

- Windows host with `signtool` available in `PATH`.
- A code-signing certificate file (for example `.pfx`) and its password.

Example configuration:

```json
{
  "sign": {
    "windows": {
      "certificate": "src/sign/windows/certificate.pfx",
      "password": "<secret>",
      "timestamp_server": "http://timestamp.digicert.com",
      "description": "MyApp",
      "url": "https://example.com"
    }
  }
}
```

Security note:

- Do not commit real passwords, tokens or private keys in `settings/release.json`.
- Put sensitive values in `settings/secrets.json` instead (loaded locally at build/sign time).

Recommended flow:

```bash
# 1) build artifacts
qyro build --target windows

# 2) validate signing prerequisites
qyro sign --check --platform windows

# 3) sign all signable binaries in build/
qyro sign --platform windows
```

By default, Qyro signs supported binary types in the freeze output (for example `.exe`, `.dll`, `.msi`, `.cab`).

#### macOS signing + notarization

Requirements:

- macOS host with Xcode Command Line Tools (`codesign`, `xcrun`, `notarytool`, `stapler`, `spctl`).
- Apple Developer membership and a valid `Developer ID Application` certificate in Keychain.
- Entitlements file for Python runtime behavior (recommended for GUI Python apps).

Example `entitlements.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
  </dict>
</plist>
```

Example configuration:

```json
{
  "sign": {
    "mac": {
      "identity": "Developer ID Application: Your Name (TEAMID)",
      "entitlements": "src/sign/mac/entitlements.plist",
      "target_architecture": "universal2",
      "notary": {
        "enabled": true,
        "staple": true,
        "assess_gatekeeper": true,
        "keychain_profile": "QYRO-NOTARY"
      }
    }
  }
}
```

Security note:

- Do not commit Apple credentials (`app_password`, API key paths, keychain profile names tied to private key workflows) in shared config files.
- Use `settings/secrets.json` for local secret overrides.

Recommended flow:

```bash
# 1) build mac app bundle
qyro build --target mac

# 2) validate signing/notary prerequisites
qyro sign --check --platform mac

# 3) sign only
qyro sign --platform mac

# 4) sign + notarize + staple
qyro sign --platform mac --notarize --staple --keychain-profile "QYRO-NOTARY"
```

Authentication options for `sign.mac.notary`:

- `keychain_profile`
- `key_path` + `key_id` (+ `issuer` for Team keys)
- `apple_id` + `team_id` + `app_password`

When `sign.mac.identity` and `sign.mac.entitlements` are configured, Qyro also forwards them to PyInstaller (`--codesign-identity` and `--osx-entitlements-file`) during `qyro build` on macOS so collected binaries are signed during packaging.

### Secret management (`settings/secrets.json`)

Qyro supports a local-only secrets file:

- `settings/secrets.json` (preferred)
- `build/settings/secrets.json` (legacy compatibility)

How it works:

- Qyro loads base/profile settings first, then applies `secrets.json` as highest-precedence overrides.
- This means values in `secrets.json` replace values from `base.json`, `release.json`, `windows.json`, `mac.json`, etc.

Repository safety:

- `settings/secrets.json` must never be committed.
- The repository `.gitignore` includes this path by default.

Example:

```json
{
  "sign": {
    "windows": {
      "password": "<local-secret>"
    },
    "mac": {
      "notary": {
        "keychain_profile": "QYRO-NOTARY-LOCAL",
        "app_password": "<local-secret>"
      }
    }
  }
}
```

---

## 🎛️ CLI Commands Reference

| Command | Flags / Args | Description |
| :--- | :--- | :--- |
| `qyro init` | `-n, --name` `-b, --binding` `--template-version` | Initialize a new project. |
| `qyro start` | none | Run the app from source. |
| `qyro build` | `-m, --mode onedir|onefile` `--onefile` `--debug` `--console` `--uac` `-p, --profile` `-c, --clean` `-i, --interactive` `--target` `--init-spec` | Freeze/build artifacts. |
| `qyro bundle` | `--release-dir` `--no-resources` `--zip` `--platform` `--format` `--check` | Create distributable packages or run preflight checks. |
| `qyro sign` | `--platform windows|mac|auto` `--check` `--notarize` `--staple` `--no-assess` `--keychain-profile` | Sign compiled artifacts and optionally notarize/staple macOS `.app`. |
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

`qyro-cli` generates apps that integrate natively with `qyro` adapters:

| Binding | Adapter | Best For |
| :--- | :--- | :--- |
| **PySide6** | `PySide6Adapter` | Modern Qt 6 desktop apps with rich widgets and tooling. |
| **PyQt6** | `PyQt6Adapter` | Feature-complete Qt 6 desktop software. |
| **PyQt5** | `PyQt5Adapter` | Legacy enterprise Qt 5 systems. |
| **PySide2** | `PySide2Adapter` | Official Qt 5 environments. |
| **Kivy** | `KivyAdapter` | Cross-platform touch interfaces for desktop/mobile. |
| **Tkinter** | `TkinterAdapter` | Zero-dependency desktop utilities built on stdlib. |
> [!WARNING]
> Mobile deployment of **Kivy** apps is still in progress. All adapters are supported on **desktop only** for now.
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
- **Ecosystem:** [Qyro](https://github.com/Neuri-AI/qyro) • [Qyro CLI](https://github.com/Neuri-AI/qyro-cli) • [Boilerplates](https://github.com/Neuri-AI)
