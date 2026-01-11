#!/bin/bash
set -euo pipefail
# Linux Wallpaper Engine GUI - Application Launcher
# This script activates the virtual environment and runs the GUI application

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the root directory of the project
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment exists (warning only; fallback to system python is supported)
if [[ ! -d "$ROOT_DIR/.venv" ]]; then
    echo -e "${YELLOW}[i]${NC} Virtual environment not found at $ROOT_DIR/.venv — the script will attempt to use system python. To create a venv run: ./install.sh"
fi

# Activate virtual environment (prefer the one managed by the installer)
VENV_PATH="$ROOT_DIR/.venv"
if [[ -f "$VENV_PATH/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_PATH/bin/activate"
    VENV_PY="$VENV_PATH/bin/python"
    echo -e "${YELLOW}[i]${NC} Activated virtualenv: $VENV_PATH"
else
    echo -e "${YELLOW}[i]${NC} Virtualenv not found at $VENV_PATH, will try system python3"
    VENV_PY="$(command -v python3 || true)"
    if [[ -z "$VENV_PY" ]]; then
        echo -e "${RED}[✗]${NC} python3 not found on PATH. Please install Python 3.10+ or create a virtualenv."
        exit 1
    fi
fi

# Enhanced backend detection - check multiple locations
detect_backend() {
    local backend_path=""
    
    # Strategy 1: Check if already in PATH
    if command -v linux-wallpaperengine >/dev/null 2>&1; then
        backend_path=$(command -v linux-wallpaperengine)
        echo -e "${GREEN}[✓]${NC} Backend found in PATH: $backend_path"
        return 0
    fi
    
    # Strategy 2: Check common installation locations
    local -a locations=(
        "$HOME/.local/bin/linux-wallpaperengine"
        "/usr/local/bin/linux-wallpaperengine"
        "/usr/bin/linux-wallpaperengine"
        "$HOME/linux-wallpaperengine/build/output/linux-wallpaperengine"
        "$ROOT_DIR/linux-wallpaperengine/build/linux-wallpaperengine"
    )
    
    for location in "${locations[@]}"; do
        if [[ -x "$location" ]]; then
            backend_path="$location"
            # Add the directory to PATH for this session
            local backend_dir
            backend_dir=$(dirname "$location")
            export PATH="$backend_dir:$PATH"
            echo -e "${GREEN}[✓]${NC} Backend found at: $backend_path"
            echo -e "${YELLOW}[i]${NC} Added $backend_dir to PATH for this session"
            return 0
        fi
    done
    
    return 1
}

# Check if linux-wallpaperengine is installed
if ! detect_backend; then
    echo -e "${RED}[✗]${NC} linux-wallpaperengine not found in PATH or common locations"
    echo ""
    echo -e "${YELLOW}[i]${NC} Searched locations:"
    echo "  - System PATH"
    echo "  - $HOME/.local/bin/"
    echo "  - /usr/local/bin/"
    echo "  - /usr/bin/"
    echo "  - $HOME/linux-wallpaperengine/build/output/"
    echo "  - $ROOT_DIR/linux-wallpaperengine/build/"
    echo ""
    echo -e "${YELLOW}[i]${NC} Install options:"
    echo "  1. Copy to ~/.local/bin: cp ~/linux-wallpaperengine/build/output/linux-wallpaperengine ~/.local/bin/"
    echo "  2. Add to PATH: export PATH=\"\$HOME/linux-wallpaperengine/build/output:\$PATH\""
    echo "  3. Install from source: https://github.com/Acters/linux-wallpaperengine"
    echo ""
    echo -e "${RED}[✗]${NC} Cannot continue without backend. Exiting."
    exit 1
fi

# Change to source directory
cd "$SCRIPT_DIR"

# Ensure GUI entry point exists
if [[ ! -f "GUI.py" ]]; then
    echo -e "${RED}[✗]${NC} GUI.py not found in $SCRIPT_DIR"
    exit 1
fi

# Trap to ensure we attempt to deactivate virtualenv on exit
trap 'deactivate 2>/dev/null || true' EXIT

# Run the application (use venv python explicitly)
echo -e "${GREEN}[✓]${NC} Starting Linux Wallpaper Engine GUI..."
PYTHONUNBUFFERED=1 "$VENV_PY" GUI.py "$@"
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo -e "${RED}[✗]${NC} GUI exited with code $EXIT_CODE"
else
    echo -e "${GREEN}[✓]${NC} GUI exited successfully"
fi

exit $EXIT_CODE
