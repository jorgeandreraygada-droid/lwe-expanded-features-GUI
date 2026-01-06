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

# Check if linux-wallpaperengine is installed
if ! command -v linux-wallpaperengine >/dev/null 2>&1; then
    echo -e "${RED}[✗]${NC} linux-wallpaperengine not found in PATH"
    echo -e "${YELLOW}[i]${NC} Install it from: https://github.com/Acters/linux-wallpaperengine"
    echo -e "${YELLOW}[i]${NC} The application will still launch but won't function properly"
    echo ""
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
