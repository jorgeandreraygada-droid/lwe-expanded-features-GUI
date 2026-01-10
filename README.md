# 🎨 Linux Wallpaper Engine Expanded Features GUI

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

**A modern, responsive graphical interface for managing dynamic wallpapers on Linux**

[Features](#-features) •
[Installation](#-installation) •
[Usage](#-usage) •
[Architecture](#-architecture) •
[Credits](#-credits) •
[Contributing](#-contributing)

</div>
### 📖 About


---

<details>
<summary>📖 About</summary>

**Linux Wallpaper Engine GUI** is a desktop application that provides an intuitive and feature-rich interface for managing and applying dynamic wallpapers on Linux systems. It leverages the power of [linux-wallpaperengine](https://github.com/Acters/linux-wallpaperengine) to bring the Wallpaper Engine experience to Linux users with additional GUI enhancements, organization tools, and automation features.
</details>

---



## ✨ Features

<details>
<summary>✨ Features</summary>

- 🖼️ **Visual Gallery** - Browse wallpapers with thumbnail previews
- 📁 **Group Organization** - Create and manage wallpaper groups/collections
- ⭐ **Favorites System** - Quick access to your preferred wallpapers
- 🎲 **Random Mode** - Automatic wallpaper rotation with customizable intervals
- ⏱️ **Delay/Timer Mode** - Set wallpapers to change at specific time intervals
- 🪟 **Window Mode** - Run wallpapers as actual windows with custom resolutions
- 🔼 **Always-on-Top Control** - Toggle window layering behavior
- � **Advanced Sound Control** - Manage audio playback with multiple sound options
- �📊 **Real-time Logging** - Monitor application and engine activity
- 💾 **Persistent Configuration** - Remember your preferences across sessions
 - 🔁 **Toggleable Sections** - Most UI panels and sections can be shown or hidden to simplify the interface and improve readability

</details>

---

## 📋 Requirements

<details>

### System Requirements
- **Operating System**: Linux (Ubuntu, Arch, Fedora, Debian, etc.)
- **Python**: 3.10 or higher
- **Display Server**: X11 (Wayland support through linux-wallpaperengine)

### System Dependencies
- `wmctrl` - Window management tool
- `xdotool` - X11 automation tool
- `python3-tk` - Tkinter GUI framework
- `python3-pil` or `python3-pillow` - Image processing library

### Backend Engine
- **[linux-wallpaperengine](https://github.com/Acters/linux-wallpaperengine)** - The core wallpaper engine
  - Install from: https://github.com/Acters/linux-wallpaperengine/tree/wayland-layer-cli
  - This is required to use wallpapers from Wallpaper Engine

---

</details>

---

## 🚀 Installation

<details>

### Automated Installation (Recommended)

```bash
git clone <repository-url>
cd linux-wallpaper-engine-features
chmod +x install.sh
# Interactive install (recommended)
./install.sh

# Non-interactive install without installing OS packages (e.g., in containers)
./install.sh --non-interactive --skip-system-deps

# Dry run to show actions without making changes
./install.sh --dry-run
```

The installer will:
1. Detect your package manager (apt, pacman, dnf, zypper)
2. Install required system dependencies (wmctrl, xdotool, python3-tk, python3-pillow) unless `--skip-system-deps` is passed
3. Create and/or activate a Python virtual environment (default: `.venv`)
4. Install Python dependencies from `requirements.txt`
5. Set executable permissions on scripts and create application directories

Installer options:
- `--skip-system-deps` — Do not attempt to install OS packages (useful on minimal or locked-down systems)
- `--non-interactive` — Do not prompt for confirmation (assume yes where reasonable)
- `--dry-run` — Show the commands that would be executed without making changes
- `--venv-path <path>` — Create virtual environment at a custom path
- `--install-backend` — Try to clone the `linux-wallpaperengine` backend if it is not found (requires `git`)

Notes:
- `tkinter` is provided by your OS package manager; it is **not** installed via pip. On Debian/Ubuntu the package is `python3-tk`, on Fedora `python3-tkinter` etc.
- If the backend `linux-wallpaperengine` is not installed you can use `--install-backend` or follow the backend's README to install it manually.
- To reproduce the exact virtual environment used by the project maintainer, the repository includes `requirements.lock.txt` with pinned package versions; `install.sh` prefers this lockfile when present and will install those exact versions to create an identical `.venv`.

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd linux-wallpaper-engine-features
   ```

2. **Install system dependencies** (choose for your distro):

   **Ubuntu/Debian**:
   ```bash
   sudo apt update
   sudo apt install -y wmctrl xdotool python3-tk python3-pil python3-venv
   ```

   **Arch Linux**:
   ```bash
   sudo pacman -Sy --noconfirm wmctrl xdotool tk python-pillow python-virtualenv
   ```

   **Fedora**:
   ```bash
   sudo dnf install -y wmctrl xdotool python3-tkinter python3-pillow python3-virtualenv
   ```

3. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up backend**:
   ```bash
   chmod +x source/core/main.sh
   mkdir -p ~/.local/share/linux-wallpaper-engine-features/
   ```

### Install linux-wallpaperengine Backend

The application requires the linux-wallpaperengine backend to function:

```bash
# Clone and install linux-wallpaperengine
git clone https://github.com/Acters/linux-wallpaperengine.git
cd linux-wallpaperengine
# Follow the installation instructions in their README
```

Ensure `linux-wallpaperengine` is installed and in your PATH.

---

</details>

---

## 🧪 Flatpak Integration (experimental)

<details>

This repository includes a Flatpak build description under the `flatpak/` directory to produce a sandboxed application bundle. The Flatpak build can be useful for testing or distributing a packaged desktop app, but it has important limitations (see notes below).

### Build & Install (example)

Build and install locally with `flatpak-builder` (developer machine):

```bash
# build and install for the current user
flatpak-builder --user --install --force-clean build-dir flatpak/x86_64-com.github.mauefrod.LWEExpandedFeaturesGUI.yml

# run the installed Flatpak
flatpak run com.github.mauefrod.LWEExpandedFeaturesGUI
```

Notes:
- The exact manifest path may vary; adjust the `.yml` filename for your architecture or manifest location in `flatpak/`.
- Flatpak builds are sandboxed and therefore may require extra permissions if you need filesystem or DBus access outside the sandbox.

### Important limitations — Flatpak is NOT RECOMMENDED for full functionality

Because Flatpak runs the application inside a sandbox, it severely limits the application's ability to detect existing windows and interact with external processes. As a result, features that depend on observing or controlling the external `linux-wallpaperengine` process (for example, the `--delay`, `--random`, `--above` flags, and reliable window detection/management) will not work correctly or reliably in the Flatpak build.

Therefore, using the Flatpak build is considered experimental. For reliable behavior and full feature support (especially automatic/random/delay modes and always-on-top/window-management flags), we strongly recommend installing and running the native build using the provided `install.sh` installer (see Installation above).

If you still wish to try the Flatpak build, treat it as best-effort and test carefully for your desktop environment and display server.

</details>

---

## 📖 Usage

<details>

### Running the Application

```bash
./source/run.sh
```

Or manually:
```bash
source .venv/bin/activate
cd source
python3 GUI.py
```

### Basic Workflow

1. **Set Wallpaper Directory**:
   - Click "PICK DIR" to select your Wallpaper Engine directory
   - Usually located at: `~/.steam/steam/steamapps/workshop/content/431960/`
   - Or your custom wallpaper collection directory

2. **Browse Wallpapers**:
   - Thumbnails will load automatically
   - Scroll through the gallery to preview available wallpapers

3. **Apply a Wallpaper**:
   - Click on any thumbnail to apply it immediately
   - The wallpaper will start running

4. **Organize with Groups**:
   - Use the group selection to filter wallpapers by category
   - Create custom groups for easier navigation

5. **Use Random Mode**:
   - Check "random mode" to enable automatic rotation
   - Set the interval (delay) between changes
   - The application will cycle through available wallpapers

6. **Configure Options**:
   - **Window Mode**: Run wallpapers as actual windows
   - **Remove Above Priority**: Remove always-on-top behavior (recommended)
   - **Show Logs**: View real-time application logs
   - **Sound Control**: Configure audio playback behavior for wallpapers
   - **Json Config**: The provided config.json in [source/core/config_example.json] is merely an example. The real
   config.json is stored at [~/.config/linux-wallpaper-engine-features/]
---

</details>

---

## 🏗️ Architecture

<details>

### Project Structure

```
linux-wallpaper-engine-features/
├── source/
│   ├── GUI.py                 # Main application entry point
│   ├── gui/                   # All GUI logic and controllers
│   │   ├── gui_engine.py      # High-level GUI controller
│   │   ├── config.py          # Configuration management and persistence
│   │   ├── wallpaper_loader.py# Thumbnail & preview loading + caching
│   │   ├── engine_controller.py# Starts/stops backend engine and manages flags
│   │   ├── event_handler/     # User event processing
   │   ├── gallery_view/      # Gallery management and rendering
│   │   └── ui_components/     # Reusable UI widgets (buttons, panels)
│   └── core/
│       └── main.sh            # Helper shell scripts used by the backend
├── install.sh                  # Native installer (recommended)
├── flatpak/                    # Flatpak manifests and build-dir (packaging)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Runtime overview

- **Process flow**: The user interacts with the UI (`GUI.py` → `gui/`), which delegates wallpaper application tasks to the `Engine Controller` (`engine_controller.py`). The controller launches and communicates with the `linux-wallpaperengine` backend (a CLI/binary) using command-line flags and by monitoring its process and logs.
- **Thumbnail & gallery**: `wallpaper_loader.py` loads `preview.jpg`/`preview.png` assets and caches thumbnails used by the `gallery_view` and `gallery_manager` to render the visual library.
- **Configuration**: `config.py` persists settings to `~/.config/linux-wallpaper-engine-features/config.json`. Installer-created data and logs are stored under `~/.local/share/linux-wallpaper-engine-features/`.
- **Window & process management**: The app uses system tools (`wmctrl`, `xdotool`) to detect and manipulate wallpaper windows when running in Window Mode or when applying `--above`/priority flags.
- **Packaging**: The `flatpak/` directory contains build manifests and an exported `build-dir` for Flatpak packaging. Flatpak builds package a runtime and sandbox the app, changing how the Engine Controller finds and interacts with external processes.

### Key components (details)

- **GUI Engine (`gui_engine.py`)**: Coordinates UI state, user actions, and high-level workflows (apply, stop, random/delay modes).
- **Engine Controller (`engine_controller.py`)**: Responsible for assembling engine command lines (`--dir`, `--window`, `--above`, `--random`, `--delay`), spawning the backend process, watching stdout/stderr for status, and terminating/cleaning up processes.
- **Wallpaper Loader (`wallpaper_loader.py`)**: Handles scanning wallpaper directories, reading preview images, generating thumbnails, and caching for responsive UI.
- **Gallery Manager / View (`gallery_view/`)**: Manages layout, selection, context menus, and commands to apply wallpapers.
- **Event Handler (`event_handler/`)**: Central event dispatcher for UI interactions and background tasks.
- **Config Manager (`config.py`)**: Loads/saves user preferences and exposes a programmatic API for settings.
- **Core scripts (`source/core/main.sh`) & `install.sh`**: Shell helpers used by the backend and the native installer; `install.sh` is the recommended way to install required system dependencies, create a virtualenv, and prepare the native environment.

### Packaging notes

- **Native build (recommended)**: `install.sh` sets up a native environment where the application has full access to system tools and processes. This results in reliable detection of existing wallpaper windows and correct behavior for `--delay`, `--random`, `--above`, and other window-management features.
- **Flatpak (experimental)**: The Flatpak build is provided for convenience/packaging in `flatpak/` but is sandboxed; sandboxing restricts filesystem, process, and window visibility which breaks or limits features that rely on interacting with external processes or the X11 window stack. For full functionality, prefer the native install.

---

</details>

---

## 🛠️ Development

<details>

### Setting Up Development Environment

```bash
git clone <repository-url>
cd linux-wallpaper-engine-features
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running in Development Mode

```bash
source .venv/bin/activate
cd source
python3 GUI.py
```

### Code Structure

The application follows an MVC-like pattern:
- **Model**: Configuration and data management
- **View**: UI components and gallery visualization
- **Controller**: GUI engine and event handlers

---

</details>

---


## 🐛 Troubleshooting

<details>

### Application won't start
- Ensure all system dependencies are installed
- Check that the virtual environment is activated
- Verify Python version is 3.10+

### Wallpapers not appearing
- Ensure linux-wallpaperengine is installed and in PATH
- Verify the wallpaper directory is correctly set
- Check that wallpaper folders contain `preview.jpg` or `preview.png`

### Wallpaper won't apply
- Test with `linux-wallpaperengine` directly
- Check logs in `~/.local/share/linux-wallpaper-engine-features/logs.txt`
- Verify your display manager compatibility

### Random/Delay mode not stopping
- The process should stop automatically; check the logs
- If stuck, kill manually: `pkill -f linux-wallpaperengine`

</details>

---

## 📝 Configuration

<details>

Configuration is stored in `~/.config/linux-wallpaper-engine-features/config.json`. You can manually edit this file to adjust settings:

- `--dir` - Wallpaper directory path
- `--window` - Window mode settings
- `--above` - Always-on-top flag
- `--random` - Random mode enabled
- `--delay` - Auto-change delay settings
- `--sound` - Audio control settings with options for silent, volume, noautomute, and no_audio_processing
- `--show-logs` - Log visibility

---


</details>


---

## 🙏 Credits & Attribution

<details>

### Original Project
This project builds upon and extends:
- **[linux-wallpaperengine](https://github.com/Acters/linux-wallpaperengine)** - A CLI tool to apply Wallpaper Engine projects on Linux
   - Created by [Acters](https://github.com/Acters)
   - A fantastic port of the Wallpaper Engine experience to Linux

### Key Technologies
- **Python 3** - Programming language
- **Tkinter** - GUI framework
- **PIL (Pillow)** - Image processing
- **linux-wallpaperengine** - Backend wallpaper engine

### Special Thanks
- The Wallpaper Engine community for creating amazing wallpapers
- The linux-wallpaperengine project for making this possible on Linux
- All contributors and users providing feedback and improvements

---

## 📄 License

<details>

This project is released under the **MIT License** - see [LICENSE](LICENSE) file for details.

</details>

---

## 🤝 Contributing

<details>

Contributions are welcome! Here's how you can help:

1. **Report Bugs** - Open an issue with details about the problem
2. **Suggest Features** - Share ideas for improvements
3. **Submit Code** - Create a pull request with your changes
4. **Improve Documentation** - Help make the docs clearer

### Development Guidelines
- Follow PEP 8 style guidelines
- Test your changes before submitting
- Provide clear commit messages
- Document any new features

</details>

---

## 📞 Support

<details>

For issues, questions, or suggestions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the logs at `~/.local/share/linux-wallpaper-engine-features/logs.txt`
3. Open an issue on the repository

</details>

---

## 🔗 Resources

<details>

- [Wallpaper Engine](https://store.steampowered.com/app/431960/Wallpaper_Engine/) - Steam Workshop
- [linux-wallpaperengine](https://github.com/Acters/linux-wallpaperengine) - Backend project
- [Python Tkinter Docs](https://docs.python.org/3/library/tkinter.html) - GUI framework documentation

</details>

---

**Made with ❤️ for the Linux community**
