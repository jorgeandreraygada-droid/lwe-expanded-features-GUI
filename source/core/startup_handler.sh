#!/bin/bash

# ==============================================================================
# STARTUP HANDLER - Linux Wallpaper Engine
# ==============================================================================
# This script is executed by systemd at user login to start the wallpaper 
# engine according to saved configuration. It sets up the environment and
# calls the Python startup manager.
#
# Called by: systemd (linux-wallpaperengine.service)
# Invoked as: /path/to/startup_handler.sh
# ==============================================================================

set -e  # Exit on any error

# Get the directory where this script is located (source/core/)
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Create log directory if it doesn't exist
LOG_DIR="$HOME/.local/share/linux-wallpaper-engine-features"
mkdir -p "$LOG_DIR"

# Log file for debugging
LOG_FILE="$LOG_DIR/logs.txt"

# Function to log messages
log_message() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [HANDLER] ${msg}" >> "$LOG_FILE"
}

# ==============================================================================
# ENVIRONMENT SETUP
# ==============================================================================

log_message "========== Startup Handler Started =========="
log_message "Script directory: $SCRIPT_DIR"
log_message "User: $(id -un) (UID: $(id -u))"
log_message "Home: $HOME"

# Set DISPLAY if not already set - handle both X11 and Wayland
if [ -z "$DISPLAY" ]; then
    # Try to find DISPLAY from a running X11 process
    for pid in $(pgrep -u $UID -f "^/usr/bin/X|^/usr/bin/Xvfb" 2>/dev/null || true); do
        export DISPLAY=$(grep -z ^DISPLAY= "/proc/$pid/environ" 2>/dev/null | sed 's/DISPLAY=//' || true)
        [ -n "$DISPLAY" ] && break
    done
    
    # Fallback to :0
    DISPLAY="${DISPLAY:-:0}"
fi
log_message "DISPLAY=$DISPLAY"

# Set XAUTHORITY - required for X11 access
if [ -z "$XAUTHORITY" ]; then
    # Try to find it from running processes
    for pid in $(pgrep -u $UID 2>/dev/null | head -5); do
        xauth_path=$(grep -z ^XAUTHORITY= "/proc/$pid/environ" 2>/dev/null | sed 's/XAUTHORITY=//' || true)
        if [ -n "$xauth_path" ] && [ -f "$xauth_path" ]; then
            export XAUTHORITY="$xauth_path"
            break
        fi
    done
    
    # Fallback to default location
    if [ -z "$XAUTHORITY" ]; then
        export XAUTHORITY="$HOME/.Xauthority"
    fi
fi
log_message "XAUTHORITY=$XAUTHORITY"

# Set D-Bus session address if not set
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    if [ -f "/run/user/$(id -u)/bus" ]; then
        export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
    fi
fi
log_message "DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"

# Set XDG_SESSION_TYPE if available
[ -n "$XDG_SESSION_TYPE" ] && log_message "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"

# ==============================================================================
# PYTHON EXECUTION
# ==============================================================================

log_message "Attempting startup..."

# Change to the script directory so main.sh can find its dependencies
cd "$SCRIPT_DIR" || {
    log_message "ERROR: Failed to change to script directory: $SCRIPT_DIR"
    exit 1
}

log_message "Working directory: $(pwd)"

# Verify Python is available
if ! command -v python3 &> /dev/null; then
    log_message "ERROR: python3 not found in PATH"
    exit 1
fi

log_message "Python: $(python3 --version)"

# Execute startup manager with error handling
if python3 << 'PYTHON_EOF'
import sys
import traceback
from pathlib import Path

try:
    # Add directories to path - SOURCE_DIR first for proper module resolution
    script_dir = '$SCRIPT_DIR'
    source_dir = str(Path(script_dir).parent)
    
    sys.path.insert(0, source_dir)
    sys.path.insert(0, script_dir)
    
    # Import and run the startup manager
    from startup_manager import run_at_startup
    run_at_startup()
    
except ImportError as e:
    print(f"[ERROR] Failed to import startup_manager: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF
then
    log_message "ERROR: Python execution failed with exit code $?"
    exit 1
fi

log_message "========== Startup Handler Completed Successfully =========="
exit 0