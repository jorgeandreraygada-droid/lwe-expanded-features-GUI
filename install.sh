#!/usr/bin/env bash
set -euo pipefail

# Minimal, robust installer for Linux Wallpaper Engine GUI
# Usage: ./install.sh [--skip-system-deps] [--non-interactive] [--dry-run] [--venv-path PATH] [--install-backend]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Defaults
VENV_PATH=".venv"
SKIP_SYSTEM_DEPS=false
NON_INTERACTIVE=false
DRY_RUN=false
INSTALL_BACKEND=false

# Helper functions
print_header() {
    echo -e "${GREEN}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

usage() {
    cat <<EOF
Usage: $0 [options]

Options:
  --skip-system-deps    Skip installing OS packages (wmctrl, xdotool, python3-tk, etc.)
  --non-interactive     Don't prompt the user and assume yes where reasonable
  --dry-run             Show what would be done without making changes
  --venv-path PATH      Location for virtual environment (default: .venv)
  --install-backend     Attempt to clone/install linux-wallpaperengine backend if not found
  -h, --help            Show this help message
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-system-deps) SKIP_SYSTEM_DEPS=true; shift;;
        --non-interactive) NON_INTERACTIVE=true; shift;;
        --dry-run) DRY_RUN=true; shift;;
        --venv-path) VENV_PATH="$2"; shift 2;;
        --install-backend) INSTALL_BACKEND=true; shift;;
        -h|--help) usage; exit 0;;
        *) print_error "Unknown option: $1"; usage; exit 1;;
    esac
done

# Dry-run helper
run_or_echo() {
    if [[ "$DRY_RUN" == true ]]; then
        echo "[DRY-RUN] $*"
    else
        eval "$@"
    fi
}

print_header "Linux Wallpaper Engine GUI - Installer"

# Basic environment checks
if [[ "$(uname -s)" != "Linux" ]]; then
    print_error "This installer is intended for Linux systems only."
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    print_error "python3 not found on PATH. Please install Python 3.10+"
    exit 1
fi

PY_VER_FULL=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
PY_MAJOR=$(echo "$PY_VER_FULL" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER_FULL" | cut -d. -f2)
if (( PY_MAJOR < 3 )) || { (( PY_MAJOR == 3 )) && (( PY_MINOR < 10 )); }; then
    print_error "Python 3.10+ is required (current: $PY_VER_FULL)."
    if [[ "$NON_INTERACTIVE" == true ]]; then
        exit 1
    else
        read -p "Continue anyway? [y/N] " answer
        [[ "$answer" =~ ^[Yy] ]] || exit 1
    fi
fi

# System dependencies installation
if [[ "$SKIP_SYSTEM_DEPS" == false ]]; then
    print_header "Installing system dependencies"
    if command -v apt >/dev/null 2>&1; then
        PKG_MANAGER="apt"
        PKG_INSTALL_CMD='sudo apt update && sudo apt install -y wmctrl xdotool python3-tk python3-pil python3-venv'
    elif command -v pacman >/dev/null 2>&1; then
        PKG_MANAGER="pacman"
        PKG_INSTALL_CMD='sudo pacman -Sy --noconfirm wmctrl xdotool tk python-pillow python-virtualenv'
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
        PKG_INSTALL_CMD='sudo dnf install -y wmctrl xdotool python3-tkinter python3-pillow python3-virtualenv'
    elif command -v zypper >/dev/null 2>&1; then
        PKG_MANAGER="zypper"
        PKG_INSTALL_CMD='sudo zypper install -y wmctrl xdotool python3-tk python3-pillow python3-virtualenv'
    else
        PKG_MANAGER="unknown"
        PKG_INSTALL_CMD=''
    fi

    if [[ "$PKG_MANAGER" == "unknown" ]]; then
        print_error "Could not detect package manager. Please install system deps manually: wmctrl, xdotool, python3-tk, python3-pillow/python3-pil, python3-venv"
        if [[ "$NON_INTERACTIVE" == true ]]; then
            print_error "Non-interactive mode: aborting due to missing package manager detection."
            exit 1
        fi
    else
        print_info "Detected package manager: $PKG_MANAGER"
        print_info "Run: $PKG_INSTALL_CMD"
        if [[ "$NON_INTERACTIVE" == false ]]; then
            read -p "Proceed to install system packages with $PKG_MANAGER? [Y/n] " ans
            ans=${ans:-Y}
        else
            ans=Y
        fi
        if [[ "$ans" =~ ^[Yy] ]]; then
            run_or_echo "$PKG_INSTALL_CMD"
            print_success "System dependencies installed (or command executed)."
        else
            print_info "Skipped system dependency installation. Ensure required packages are installed manually."
        fi
    fi
else
    print_info "Skipping system dependencies as requested."
fi

# Virtual environment
print_header "Python virtual environment"
print_info "Virtual environment path: $VENV_PATH"
if [[ ! -d "$VENV_PATH" ]]; then
    run_or_echo "python3 -m venv \"$VENV_PATH\""
    print_success "Virtual environment created at $VENV_PATH"
else
    print_info "Virtual environment already exists"
fi

print_info "Activating virtual environment"
if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] source \"$VENV_PATH/bin/activate\""
else
    # shellcheck disable=SC1091
    source "$VENV_PATH/bin/activate"
fi

print_info "Upgrading pip/setuptools/wheel"
run_or_echo "pip install --upgrade pip setuptools wheel"

# Install Python requirements (prefer exact lock if present)
print_header "Python dependencies"
if [[ -f "requirements.lock.txt" ]]; then
    print_info "Found requirements.lock.txt — installing exact pinned versions to reproduce the developer venv"
    run_or_echo "pip install -r requirements.lock.txt"
    print_success "Installed exact Python packages from requirements.lock.txt"
elif [[ -f "requirements.txt" ]]; then
    print_info "Installing from requirements.txt (floating/ranged versions)"
    run_or_echo "pip install -r requirements.txt"
    print_success "Installed Python packages from requirements.txt"
else
    print_error "No requirements file found in project root. Aborting."
    exit 1
fi

# Make scripts executable
print_header "Fixing permissions"
if [[ -f "source/core/main.sh" ]]; then
    run_or_echo "chmod +x source/core/main.sh"
    print_success "Set executable bit on source/core/main.sh"
else
    print_info "source/core/main.sh not found (skipping)"
fi

if [[ -f "source/core/lwe-state-manager.sh" ]]; then
    run_or_echo "chmod +x source/core/lwe-state-manager.sh"
    print_success "Set executable bit on source/core/lwe-state-manager.sh"
else
    print_info "source/core/lwe-state-manager.sh not found (skipping)"
fi

if [[ -f "source/run.sh" ]]; then
    run_or_echo "chmod +x source/run.sh"
    print_success "Set executable bit on source/run.sh"
else
    print_info "source/run.sh not found (skipping)"
fi

run_or_echo "chmod +x install.sh || true"

# Install helper scripts to system paths (optional, with sudo if needed)
print_header "Installing helper scripts (optional)"
if [[ -f "flatpak/lwe-window-manager.sh" ]]; then
    INSTALL_DIR="/usr/local/bin"
    if [[ -w "$INSTALL_DIR" ]]; then
        # Writable without sudo
        run_or_echo "cp flatpak/lwe-window-manager.sh $INSTALL_DIR/"
        run_or_echo "chmod +x $INSTALL_DIR/lwe-window-manager.sh"
        print_success "Installed lwe-window-manager.sh to $INSTALL_DIR/"
    else
        # Need sudo
        if command -v sudo >/dev/null 2>&1; then
            if [[ "$NON_INTERACTIVE" == false ]]; then
                echo ""
                read -p "lwe-window-manager.sh needs to be installed to $INSTALL_DIR (requires sudo). Continue? [Y/n] " ans_install
                ans_install=${ans_install:-Y}
            else
                ans_install=Y
            fi
            if [[ "$ans_install" =~ ^[Yy] ]]; then
                if [[ "$DRY_RUN" == true ]]; then
                    echo "[DRY-RUN] sudo cp flatpak/lwe-window-manager.sh $INSTALL_DIR/"
                    echo "[DRY-RUN] sudo chmod +x $INSTALL_DIR/lwe-window-manager.sh"
                else
                    sudo cp flatpak/lwe-window-manager.sh "$INSTALL_DIR/" && \
                    sudo chmod +x "$INSTALL_DIR/lwe-window-manager.sh" && \
                    print_success "Installed lwe-window-manager.sh to $INSTALL_DIR/"
                fi
            fi
        else
            print_info "sudo not found; skipping privileged install. Manual installation:"
            echo "  sudo cp flatpak/lwe-window-manager.sh /usr/local/bin/"
            echo "  sudo chmod +x /usr/local/bin/lwe-window-manager.sh"
        fi
    fi
else
    print_info "flatpak/lwe-window-manager.sh not found (skipping)"
fi

# Create standard directories
print_header "Creating application directories"
run_or_echo "mkdir -p ~/.local/share/linux-wallpaper-engine-features/"
run_or_echo "mkdir -p ~/.config/linux-wallpaper-engine-features/"
print_success "Application directories ensured"

# Check for linux-wallpaperengine backend (IMPROVED DETECTION)
print_header "Checking linux-wallpaperengine backend"

BACKEND_FOUND=false
BACKEND_PATH=""

# Method 1: Check common binary names in PATH
for binary_name in linux-wallpaperengine wallpaperengine; do
    if command -v "$binary_name" >/dev/null 2>&1; then
        BACKEND_PATH=$(command -v "$binary_name")
        print_success "$binary_name found in PATH: $BACKEND_PATH"
        
        # Try to get version info
        VERSION_INFO=$("$binary_name" --version 2>/dev/null || echo "version unknown")
        print_info "Version: $VERSION_INFO"
        
        BACKEND_FOUND=true
        break
    fi
done

# Method 2: Check common installation locations
if [[ "$BACKEND_FOUND" == false ]]; then
    print_info "Not found in PATH, checking common installation locations..."
    
    for location in \
        "$HOME/.local/bin/linux-wallpaperengine" \
        "/usr/local/bin/linux-wallpaperengine" \
        "/usr/bin/linux-wallpaperengine" \
        "./linux-wallpaperengine/build/linux-wallpaperengine" \
        "$HOME/linux-wallpaperengine/build/output/linux-wallpaperengine" \
        "./linux-wallpaperengine/linux-wallpaperengine"; do
        
        if [[ -x "$location" ]]; then
            BACKEND_PATH="$location"
            print_success "Backend found at: $BACKEND_PATH"
            
            # Check if it's in PATH
            if [[ "$location" == "./"* ]]; then
                print_info "NOTE: Backend is in local directory. Consider adding $(dirname "$(readlink -f "$location")") to your PATH"
            elif [[ "$location" == "$HOME/.local/bin/"* ]]; then
                print_info "NOTE: Ensure $HOME/.local/bin is in your PATH"
            fi
            
            BACKEND_FOUND=true
            break
        fi
    done
fi

# If still not found, provide detailed diagnostics
if [[ "$BACKEND_FOUND" == false ]]; then
    print_error "linux-wallpaperengine backend not found"
    echo ""
    print_info "Checked the following locations:"
    echo "  - System PATH (as 'linux-wallpaperengine' or 'wallpaperengine')"
    echo "  - $HOME/.local/bin/linux-wallpaperengine"
    echo "  - /usr/local/bin/linux-wallpaperengine"
    echo "  - /usr/bin/linux-wallpaperengine"
    echo "  - ./linux-wallpaperengine/build/linux-wallpaperengine"
    echo ""
    
    # Offer to install backend
    if [[ "$INSTALL_BACKEND" == true ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY-RUN] git clone https://github.com/Acters/linux-wallpaperengine.git"
        else
            if ! command -v git >/dev/null 2>&1; then
                print_error "git is required to clone the backend. Install git and retry."
            else
                print_info "Cloning linux-wallpaperengine to ./linux-wallpaperengine"
                if git clone https://github.com/Acters/linux-wallpaperengine.git; then
                    print_success "Backend repository cloned successfully"
                    echo ""
                    print_info "To build and install the backend:"
                    echo "  cd linux-wallpaperengine"
                    echo "  mkdir build && cd build"
                    echo "  cmake .."
                    echo "  make"
                    echo "  sudo make install  # or copy the binary to ~/.local/bin/"
                    echo ""
                    print_info "Then re-run this installer to verify the installation"
                else
                    print_error "Failed to clone backend repository"
                fi
            fi
        fi
    else
        print_info "Installation options:"
        echo ""
        echo "  Option 1: Re-run with --install-backend to clone the repository"
        echo "    ./install.sh --install-backend"
        echo ""
        echo "  Option 2: Manual installation from source"
        echo "    git clone https://github.com/Acters/linux-wallpaperengine.git"
        echo "    cd linux-wallpaperengine"
        echo "    mkdir build && cd build"
        echo "    cmake .."
        echo "    make"
        echo "    sudo make install"
        echo ""
        echo "  Option 3: Check if your distribution has a package"
        echo "    Arch (AUR): yay -S linux-wallpaperengine-git"
        echo ""
    fi
    
    # Diagnostic commands
    print_info "To diagnose backend installation issues, run:"
    echo "  which linux-wallpaperengine"
    echo "  echo \$PATH"
    echo "  ls -la ~/.local/bin/linux-wallpaperengine 2>/dev/null"
    echo "  ls -la /usr/local/bin/linux-wallpaperengine 2>/dev/null"
fi

# Optional: create desktop entry
print_header "Desktop entry (optional)"
DESKTOP_FILE="$HOME/.local/share/applications/linux-wallpaper-engine-features.desktop"
if [[ -f "$DESKTOP_FILE" ]]; then
    print_info "Desktop entry already exists: $DESKTOP_FILE"
else
    if [[ "$NON_INTERACTIVE" == false ]]; then
        read -p "Create a desktop entry to launch the app from the menu? [Y/n] " ans2
        ans2=${ans2:-Y}
    else
        ans2=Y
    fi
    if [[ "$ans2" =~ ^[Yy] ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY-RUN] create $DESKTOP_FILE"
        else
            cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Linux Wallpaper Engine GUI
Exec=$PWD/source/run.sh
Terminal=false
Type=Application
Icon=preferences-desktop-wallpaper
Categories=Utility;Graphics;
EOF
            print_success "Created desktop entry: $DESKTOP_FILE"
        fi
    fi
fi

# Final summary
print_header "Installation complete"
print_success "Installer finished"

echo ""
if [[ "$BACKEND_FOUND" == true ]]; then
    print_success "Backend detected at: $BACKEND_PATH"
else
    print_error "Backend NOT detected - you must install linux-wallpaperengine before using this GUI"
fi

echo ""
print_info "Next steps:"
if [[ "$BACKEND_FOUND" == false ]]; then
    echo "  1. Install linux-wallpaperengine backend (see instructions above)"
    echo "  2. Re-run this installer to verify: ./install.sh"
    echo "  3. Launch the app: $PWD/source/run.sh"
else
    echo "  - Launch the app: $PWD/source/run.sh (or from the desktop menu if created)"
    echo "  - To run inside the virtualenv: source $VENV_PATH/bin/activate && python3 source/GUI.py"
fi

echo ""
print_info "For details see README.md and INSTALL_NOTES.md"

# Deactivate if we activated
if [[ "$DRY_RUN" != true ]]; then
    deactivate 2>/dev/null || true
fi

exit 0
