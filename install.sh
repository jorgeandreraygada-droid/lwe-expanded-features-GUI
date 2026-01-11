#!/usr/bin/env bash
set -euo pipefail

# Minimal, robust installer for Linux Wallpaper Engine GUI
# Usage: ./install.sh [--skip-system-deps] [--non-interactive] [--dry-run] [--venv-path PATH] [--install-backend]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[→]${NC} $1"
}

usage() {
    cat <<EOF
Usage: $0 [options]

Options:
  --skip-system-deps    Skip installing OS packages (wmctrl, xdotool, python3-tk, etc.)
  --non-interactive     Don't prompt the user and assume yes where reasonable
  --dry-run             Show what would be done without making changes
  --venv-path PATH      Location for virtual environment (default: .venv)
  --install-backend     Auto-install linux-wallpaperengine backend locally if not found
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

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/linux-wallpaperengine"
BACKEND_BUILD_DIR="$BACKEND_DIR/build"
BACKEND_BINARY="$BACKEND_BUILD_DIR/linux-wallpaperengine"

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

# Detect package manager (only once, used throughout the script)
detect_package_manager() {
    if command -v apt >/dev/null 2>&1; then
        echo "apt"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v zypper >/dev/null 2>&1; then
        echo "zypper"
    else
        echo "unknown"
    fi
}

# Get package list for a specific manager
get_packages() {
    local manager="$1"
    local package_type="$2"  # "gui" or "backend"
    
    case "$manager" in
        apt)
            if [[ "$package_type" == "gui" ]]; then
                echo "wmctrl xdotool python3-tk python3-pil python3-venv"
            else
                echo "build-essential cmake libglm-dev libsdl2-dev libmpv-dev liblz4-dev libzstd-dev libglew-dev libavcodec-dev libavformat-dev libavutil-dev git"
            fi
            ;;
        pacman)
            if [[ "$package_type" == "gui" ]]; then
                echo "wmctrl xdotool tk python-pillow python-virtualenv"
            else
                echo "base-devel cmake glm sdl2 mpv lz4 zstd glew ffmpeg git"
            fi
            ;;
        dnf)
            if [[ "$package_type" == "gui" ]]; then
                echo "wmctrl xdotool python3-tkinter python3-pillow python3-virtualenv"
            else
                echo "gcc-c++ cmake glm-devel SDL2-devel mpv-devel lz4-devel libzstd-devel glew-devel ffmpeg-devel git"
            fi
            ;;
        zypper)
            if [[ "$package_type" == "gui" ]]; then
                echo "wmctrl xdotool python3-tk python3-pillow python3-virtualenv"
            else
                echo "gcc-c++ cmake glm-devel libSDL2-devel mpv-devel lz4-devel libzstd-devel glew-devel ffmpeg-devel git"
            fi
            ;;
        *)
            echo ""
            ;;
    esac
}

# Build install command for a specific manager
get_install_command() {
    local manager="$1"
    local packages="$2"
    
    case "$manager" in
        apt)
            echo "sudo apt update && sudo apt install -y $packages"
            ;;
        pacman)
            echo "sudo pacman -Sy --noconfirm $packages"
            ;;
        dnf)
            echo "sudo dnf install -y $packages"
            ;;
        zypper)
            echo "sudo zypper install -y $packages"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Detect package manager once
PKG_MANAGER=$(detect_package_manager)
print_info "Detected package manager: $PKG_MANAGER"

# System dependencies installation
if [[ "$SKIP_SYSTEM_DEPS" == false ]]; then
    print_header "Installing system dependencies"
    
    if [[ "$PKG_MANAGER" == "unknown" ]]; then
        print_error "Could not detect package manager."
        print_info "Please install these dependencies manually:"
        echo "  GUI: wmctrl, xdotool, python3-tk, python3-pillow, python3-venv"
        echo "  Backend: build-essential/base-devel, cmake, glm, SDL2, mpv, lz4, zstd, glew, ffmpeg, git"
        if [[ "$NON_INTERACTIVE" == true ]]; then
            print_error "Non-interactive mode: aborting due to missing package manager detection."
            exit 1
        fi
    else
        GUI_DEPS=$(get_packages "$PKG_MANAGER" "gui")
        BACKEND_DEPS=$(get_packages "$PKG_MANAGER" "backend")
        ALL_DEPS="$GUI_DEPS $BACKEND_DEPS"
        PKG_INSTALL_CMD=$(get_install_command "$PKG_MANAGER" "$ALL_DEPS")
        
        print_info "Will install: GUI + Backend build dependencies"
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
    print_info "Found requirements.lock.txt — installing exact pinned versions"
    run_or_echo "pip install -r requirements.lock.txt"
    print_success "Installed exact Python packages from requirements.lock.txt"
elif [[ -f "requirements.txt" ]]; then
    print_info "Installing from requirements.txt"
    run_or_echo "pip install -r requirements.txt"
    print_success "Installed Python packages from requirements.txt"
else
    print_error "No requirements file found in project root. Aborting."
    exit 1
fi

# Make scripts executable
print_header "Fixing permissions"
for script in "source/core/main.sh" "source/core/lwe-state-manager.sh" "source/run.sh" "install.sh"; do
    if [[ -f "$script" ]]; then
        run_or_echo "chmod +x $script"
        print_success "Set executable bit on $script"
    fi
done

# Install helper scripts to system paths (optional, with sudo if needed)
print_header "Installing helper scripts (optional)"
if [[ -f "flatpak/lwe-window-manager.sh" ]]; then
    INSTALL_DIR="/usr/local/bin"
    if [[ -w "$INSTALL_DIR" ]]; then
        run_or_echo "cp flatpak/lwe-window-manager.sh $INSTALL_DIR/"
        run_or_echo "chmod +x $INSTALL_DIR/lwe-window-manager.sh"
        print_success "Installed lwe-window-manager.sh to $INSTALL_DIR/"
    else
        if command -v sudo >/dev/null 2>&1; then
            if [[ "$NON_INTERACTIVE" == false ]]; then
                echo ""
                read -p "lwe-window-manager.sh needs sudo to install to $INSTALL_DIR. Continue? [Y/n] " ans_install
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
        fi
    fi
fi

# Create standard directories
print_header "Creating application directories"
run_or_echo "mkdir -p ~/.local/share/linux-wallpaper-engine-features/"
run_or_echo "mkdir -p ~/.config/linux-wallpaper-engine-features/"
print_success "Application directories ensured"

# Check for linux-wallpaperengine backend (IMPROVED WITH AUTO-INSTALL)
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

# Method 2: Check project-local installation
if [[ "$BACKEND_FOUND" == false ]] && [[ -x "$BACKEND_BINARY" ]]; then
    BACKEND_PATH="$BACKEND_BINARY"
    print_success "Backend found in project: $BACKEND_PATH"
    BACKEND_FOUND=true
fi

# Method 3: Check common installation locations
if [[ "$BACKEND_FOUND" == false ]]; then
    print_info "Not found in PATH or project, checking system locations..."
    
    for location in \
        "$HOME/.local/bin/linux-wallpaperengine" \
        "/usr/local/bin/linux-wallpaperengine" \
        "/usr/bin/linux-wallpaperengine" \
        "$HOME/linux-wallpaperengine/build/output/linux-wallpaperengine"; do
        
        if [[ -x "$location" ]]; then
            BACKEND_PATH="$location"
            print_success "Backend found at: $BACKEND_PATH"
            BACKEND_FOUND=true
            break
        fi
    done
fi

# AUTO-INSTALL BACKEND IF NOT FOUND
if [[ "$BACKEND_FOUND" == false ]]; then
    print_error "linux-wallpaperengine backend not found"
    echo ""
    
    # Determine if we should auto-install
    SHOULD_INSTALL=false
    
    if [[ "$INSTALL_BACKEND" == true ]]; then
        SHOULD_INSTALL=true
    elif [[ "$NON_INTERACTIVE" == false ]]; then
        echo -e "${YELLOW}Would you like to automatically build and install linux-wallpaperengine locally?${NC}"
        echo "This will:"
        echo "  - Clone the repository to: $BACKEND_DIR"
        echo "  - Build the backend (takes 2-5 minutes)"
        echo "  - Keep it isolated within this project"
        echo ""
        read -p "Auto-install backend? [Y/n] " ans_backend
        ans_backend=${ans_backend:-Y}
        if [[ "$ans_backend" =~ ^[Yy] ]]; then
            SHOULD_INSTALL=true
        fi
    fi
    
    if [[ "$SHOULD_INSTALL" == true ]]; then
        print_header "Building linux-wallpaperengine locally"
        
        # Check for required tools
        if ! command -v git >/dev/null 2>&1; then
            print_error "git is required but not found. Please install git first."
            exit 1
        fi
        
        if ! command -v cmake >/dev/null 2>&1; then
            print_error "cmake is required but not found. Please install build dependencies first."
            exit 1
        fi
        
        # Clone repository if not exists
        if [[ ! -d "$BACKEND_DIR" ]]; then
            print_step "Cloning linux-wallpaperengine repository..."
            if [[ "$DRY_RUN" == true ]]; then
                echo "[DRY-RUN] git clone https://github.com/Acters/linux-wallpaperengine.git $BACKEND_DIR"
            else
                if git clone https://github.com/Acters/linux-wallpaperengine.git "$BACKEND_DIR"; then
                    print_success "Repository cloned successfully"
                else
                    print_error "Failed to clone repository"
                    exit 1
                fi
            fi
        else
            print_info "Repository already exists at $BACKEND_DIR"
            
            # Offer to update
            if [[ "$NON_INTERACTIVE" == false ]]; then
                read -p "Update repository to latest version? [y/N] " ans_update
                if [[ "$ans_update" =~ ^[Yy] ]]; then
                    print_step "Updating repository..."
                    if [[ "$DRY_RUN" == false ]]; then
                        (cd "$BACKEND_DIR" && git pull) || print_error "Failed to update repository"
                    fi
                fi
            fi
        fi
        
        # Build the backend
        print_step "Building linux-wallpaperengine (this may take a few minutes)..."
        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY-RUN] mkdir -p $BACKEND_BUILD_DIR"
            echo "[DRY-RUN] cd $BACKEND_BUILD_DIR && cmake .. && make -j\$(nproc)"
        else
            # Create build directory
            mkdir -p "$BACKEND_BUILD_DIR"
            
            # Configure with CMake
            print_step "Configuring with CMake..."
            if ! (cd "$BACKEND_BUILD_DIR" && cmake ..); then
                print_error "CMake configuration failed"
                echo ""
                print_info "Make sure you have all build dependencies installed:"
                echo "  - build-essential (gcc, g++, make)"
                echo "  - cmake"
                echo "  - libglm-dev, libsdl2-dev, libmpv-dev"
                echo "  - liblz4-dev, libzstd-dev, libglew-dev"
                echo "  - libavcodec-dev, libavformat-dev, libavutil-dev"
                exit 1
            fi
            
            # Build with make
            print_step "Compiling (using all CPU cores)..."
            if ! (cd "$BACKEND_BUILD_DIR" && make -j"$(nproc)"); then
                print_error "Build failed"
                exit 1
            fi
            
            # Verify binary was created
            if [[ -x "$BACKEND_BINARY" ]]; then
                print_success "Backend built successfully: $BACKEND_BINARY"
                
                # Get version
                VERSION_INFO=$("$BACKEND_BINARY" --version 2>/dev/null || echo "version unknown")
                print_info "Version: $VERSION_INFO"
                
                BACKEND_FOUND=true
                BACKEND_PATH="$BACKEND_BINARY"
            else
                print_error "Build completed but binary not found at expected location"
                exit 1
            fi
        fi
    else
        # User declined auto-install
        echo ""
        print_info "Installation options:"
        echo ""
        echo "  Option 1: Re-run installer with auto-install"
        echo "    ./install.sh --install-backend"
        echo ""
        echo "  Option 2: Manual installation"
        echo "    git clone https://github.com/Acters/linux-wallpaperengine.git"
        echo "    cd linux-wallpaperengine"
        echo "    mkdir build && cd build"
        echo "    cmake .."
        echo "    make -j\$(nproc)"
        echo "    sudo make install"
        echo ""
        echo "  Option 3: Distribution package (if available)"
        echo "    Arch (AUR): yay -S linux-wallpaperengine-git"
        echo ""
        print_error "Cannot continue without backend"
        exit 1
    fi
fi

# Desktop entry management (with cleanup of old entries)
print_header "Desktop entry management"
DESKTOP_FILE="$HOME/.local/share/applications/linux-wallpaper-engine-features.desktop"
DESKTOP_DIR="$HOME/.local/share/applications"

# Clean up any old/broken desktop entries
if [[ -f "$DESKTOP_FILE" ]]; then
    print_info "Found existing desktop entry"
    
    # Check if the Exec path in the old entry still exists
    if [[ "$DRY_RUN" == false ]]; then
        OLD_EXEC=$(grep "^Exec=" "$DESKTOP_FILE" 2>/dev/null | cut -d= -f2- | cut -d' ' -f1 || echo "")
        
        if [[ -n "$OLD_EXEC" ]] && [[ ! -f "$OLD_EXEC" ]]; then
            print_info "Old desktop entry points to missing file: $OLD_EXEC"
            print_step "Removing outdated desktop entry..."
            rm -f "$DESKTOP_FILE"
            print_success "Removed outdated desktop entry"
        elif [[ -n "$OLD_EXEC" ]] && [[ "$OLD_EXEC" != "$PROJECT_ROOT/source/run.sh" ]]; then
            print_info "Old desktop entry points to different installation: $OLD_EXEC"
            print_step "Updating desktop entry to current installation..."
            rm -f "$DESKTOP_FILE"
            print_success "Removed old desktop entry"
        else
            print_info "Desktop entry is up to date"
        fi
    fi
fi

# Create/recreate desktop entry
if [[ ! -f "$DESKTOP_FILE" ]]; then
    if [[ "$NON_INTERACTIVE" == false ]]; then
        read -p "Create a desktop entry to launch from the menu? [Y/n] " ans2
        ans2=${ans2:-Y}
    else
        ans2=Y
    fi
    
    if [[ "$ans2" =~ ^[Yy] ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY-RUN] create $DESKTOP_FILE"
        else
            mkdir -p "$DESKTOP_DIR"
            cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Linux Wallpaper Engine GUI
Comment=GUI for managing animated wallpapers with linux-wallpaperengine
Exec=$PROJECT_ROOT/source/run.sh
Path=$PROJECT_ROOT
Terminal=false
Type=Application
Icon=preferences-desktop-wallpaper
Categories=Utility;Graphics;Settings;
StartupNotify=false
X-GNOME-UsesNotifications=false
EOF
            chmod +x "$DESKTOP_FILE"
            
            # Update desktop database to refresh menu
            if command -v update-desktop-database >/dev/null 2>&1; then
                update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
            fi
            
            print_success "Created desktop entry: $DESKTOP_FILE"
            print_info "Application should now appear in your application menu"
        fi
    fi
else
    print_success "Desktop entry is current: $DESKTOP_FILE"
fi

# Final summary
print_header "Installation complete"

echo ""
if [[ "$BACKEND_FOUND" == true ]]; then
    print_success "✓ Backend installed: $BACKEND_PATH"
    
    # Show if it's local or system
    if [[ "$BACKEND_PATH" == "$PROJECT_ROOT"* ]]; then
        print_info "Backend is installed locally within this project (isolated installation)"
    else
        print_info "Backend is installed system-wide"
    fi
else
    print_error "✗ Backend NOT installed"
fi

print_success "✓ Python virtual environment configured"
print_success "✓ GUI application ready"

echo ""
print_header "Next steps"
echo "  Launch the application:"
echo "    $PROJECT_ROOT/source/run.sh"
echo ""
echo "  Or from the desktop menu if you created the entry"
echo ""
print_info "Logs are stored in: ~/.local/share/linux-wallpaper-engine-features/logs.txt"
print_info "For more details see: README.md and INSTALL_NOTES.md"

# Deactivate if we activated
if [[ "$DRY_RUN" != true ]]; then
    deactivate 2>/dev/null || true
fi

echo ""
print_success "Installation successful! Enjoy your animated wallpapers! 🎨"

exit 0
