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

---

## 📖 About

**Linux Wallpaper Engine GUI** is a desktop application that provides an intuitive and feature-rich interface for managing and applying dynamic wallpapers on Linux systems. It leverages the power of [linux-wallpaperengine](https://github.com/Acters/linux-wallpaperengine) to bring the Wallpaper Engine experience to Linux users with additional GUI enhancements, organization tools, and automation features.

---

## ✨ Features

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

---

## 📋 Requirements

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

## 🚀 Installation

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

## 📖 Usage

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

### Sound Control (--sound)

The Sound Control panel allows you to manage audio playback from wallpapers with several options:

#### Available Sound Options

1. **Silent Mode** (`--silent`)
   - Completely mutes all audio output from the wallpaper
   - Useful when you want visual wallpapers without sound
   - Affects only the wallpaper engine, not your system audio

2. **No Auto Mute** (`--noautomute`)
   - Prevents the wallpaper from automatically muting its audio when other applications play sound
   - By default, wallpapers mute themselves when you play music, watch videos, etc.
   - Enable this to keep wallpaper audio active even when other apps are playing audio

3. **No Audio Processing** (`--no-audio-processing`)
   - Disables audio-reactive features in wallpapers
   - Some wallpapers respond to audio input (visualization, color changes, animations based on sound)
   - Use this option to disable those features and improve performance

#### How Sound Control Works in the GUI

**Panel Behavior**:
- The Sound Control panel is located in the right sidebar below the Flags panel
- Each option is presented as an independent checkbox
- All checkboxes can be used together or independently
- Settings are automatically saved to `~/.config/linux-wallpaper-engine-features/config.json`

**Event Handling**:
- When you toggle any sound checkbox, an event handler is triggered
- The handler updates the configuration file with the new sound settings
- If a wallpaper is currently active, it is automatically re-applied with the updated audio configuration
- This ensures sound changes take effect immediately without requiring manual wallpaper reapplication

**Backend Integration**:
- The [source/gui/event_handler/event_handler.py](source/gui/event_handler/event_handler.py) handles all sound checkbox changes
- Sound flags are collected and passed to the backend shell script [source/core/main.sh](source/core/main.sh)
- The `--sound` flag groups all audio-related options and passes them directly to the `linux-wallpaperengine` backend
- The backend engine interprets and applies these sound parameters to the wallpaper process

**Configuration Storage**:
Sound settings are stored in your config file under the `--sound` object:
```json
"--sound": {
  "silent": false,
  "volume": null,
  "noautomute": false,
  "no_audio_processing": false
}
```

#### Example Usage Scenarios

- **Quiet Desktop**: Enable `Silent` to mute all wallpaper audio while maintaining visual quality
- **Ambient Audio**: Leave `No Auto Mute` unchecked (default) to let wallpapers auto-mute when you're playing music
- **Always-On Audio**: Enable `No Auto Mute` if you want wallpaper audio to continue playing in the background regardless of other apps
- **Performance**: Enable `No Audio Processing` if your CPU usage is high from audio-reactive animations
- **Custom Combinations**: Mix and match options to suit your preference (e.g., silent + no audio processing for minimal overhead)

---

## 🏗️ Architecture

### Project Structure

```
linux-wallpaper-engine-features/
├── source/
│   ├── GUI.py                 # Main application entry point
│   ├── gui/
│   │   ├── gui_engine.py      # GUI controller
│   │   ├── config.py          # Configuration management
│   │   ├── wallpaper_loader.py# Image loading and caching
│   │   ├── engine_controller.py# Backend process management
│   │   ├── event_handler/     # Event handling system
│   │   ├── ui_components/     # UI components (buttons, panels)
│   │   ├── gallery_view/      # Gallery management and rendering
│   │   └── groups.py          # Group management
│   └── core/
│       └── main.sh            # Backend shell script
├── install.sh                  # Installation script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Key Components

- **GUI Engine** - Main controller coordinating all UI components
- **Gallery Manager** - Handles thumbnail rendering and layout
- **Engine Controller** - Manages backend process execution
- **Event Handler** - Processes user interactions
- **Config Manager** - Saves/loads user preferences

---

## 🛠️ Development

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

## 🐛 Troubleshooting

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

---

## 📝 Configuration

Configuration is stored in `~/.config/linux-wallpaper-engine-features/config.json`. You can manually edit this file to adjust settings:

- `--dir` - Wallpaper directory path
- `--window` - Window mode settings
- `--above` - Always-on-top flag
- `--random` - Random mode enabled
- `--delay` - Auto-change delay settings
- `--sound` - Audio control settings with options for silent, volume, noautomute, and no_audio_processing
- `--show-logs` - Log visibility

#### Sound Configuration Options

The `--sound` configuration object contains:

```json
"--sound": {
  "silent": false,              // Mute all wallpaper audio
  "volume": null,               // Volume level (0-100, null means use default) *Currently not supported. Ignore in config file.
  "noautomute": false,          // Don't auto-mute when other apps play audio
  "no_audio_processing": false  // Disable audio-reactive features
}
```

---

## 🙏 Credits & Attribution

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

This project is released under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

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

---

## 📞 Support

For issues, questions, or suggestions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the logs at `~/.local/share/linux-wallpaper-engine-features/logs.txt`
3. Open an issue on the repository

---

## 🔗 Resources

- [Wallpaper Engine](https://store.steampowered.com/app/431960/Wallpaper_Engine/) - Steam Workshop
- [linux-wallpaperengine](https://github.com/Acters/linux-wallpaperengine) - Backend project
- [Python Tkinter Docs](https://docs.python.org/3/library/tkinter.html) - GUI framework documentation

---

**Made with ❤️ for the Linux community**
