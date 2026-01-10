#!/bin/bash
# window-monitor.sh
# Background daemon to monitor and manipulate LWE windows
# ENHANCED FOR FLATPAK: Uses multiple strategies to detect and manipulate windows
# Includes X11 sync, XDotool fallbacks, and process-based detection
#
# Usage: window-monitor.sh <pid> <remove_above> [log_file] [app_id]

set -euo pipefail

ENGINE_PID="${1:-}"
REMOVE_ABOVE="${2:-false}"
LOG_FILE="${3:-}"
FLATPAK_APP_ID="${4:-}"

if [[ -z "$ENGINE_PID" ]]; then
    exit 1
fi

# Detect if running in Flatpak
IN_FLATPAK=false
if [[ -f /.flatpak-info ]]; then
    IN_FLATPAK=true
fi

# Non-blocking logging
log_monitor() {
    if [[ -n "$LOG_FILE" ]] && [[ -w "$LOG_FILE" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MONITOR-$$] $*" >> "$LOG_FILE" &
    fi
}

# Force X11 server to sync with pending events
sync_x11() {
    # Force X11 server to process all pending events
    if command -v xdotool >/dev/null 2>&1; then
        timeout 1 xdotool getactivewindow >/dev/null 2>&1 || true
    fi
    # Give X11 server time to process
    sleep 0.1
}

# Get window ID by searching for process windows
get_window_for_pid() {
    local pid="$1"
    local attempts=0
    local max_attempts=5
    
    while [[ $attempts -lt $max_attempts ]]; do
        # Try wmctrl with process matching
        if command -v wmctrl >/dev/null 2>&1; then
            local win_id
            win_id=$(wmctrl -lp 2>/dev/null | awk -v p="$pid" '$3 == p {print $1; exit}' || true)
            if [[ -n "$win_id" ]]; then
                echo "$win_id"
                return 0
            fi
        fi
        
        # Try xdotool with search
        if command -v xdotool >/dev/null 2>&1; then
            local win_id
            win_id=$(xdotool search --pid "$pid" 2>/dev/null | head -1 || true)
            if [[ -n "$win_id" ]]; then
                echo "$win_id"
                return 0
            fi
        fi
        
        attempts=$((attempts + 1))
        sleep 0.2
    done
    
    return 1
}

# Apply window flags with robust retry logic
apply_window_flags() {
    local win_id="$1"
    local retry_count=0
    local max_retries=5
    
    # Ensure X11 is synced before trying to modify windows
    sync_x11
    
    while [[ $retry_count -lt $max_retries ]]; do
        # Method 1: wmctrl remove above
        if command -v wmctrl >/dev/null 2>&1; then
            if wmctrl -i -r "$win_id" -b remove,above 2>/dev/null; then
                log_monitor "Successfully removed 'above' flag via wmctrl (attempt $((retry_count + 1)))"
                
                # Also add skip_pager and below
                wmctrl -i -r "$win_id" -b add,skip_pager 2>/dev/null || true
                wmctrl -i -r "$win_id" -b add,below 2>/dev/null || true
                return 0
            fi
        fi
        
        # Method 2: xdotool with state manipulation
        if command -v xdotool >/dev/null 2>&1; then
            # Get current state and try to modify
            if timeout 0.5 xdotool windowactivate --sync "$win_id" 2>/dev/null; then
                # xdotool doesn't have direct "remove above", but activating can help
                # Try wmctrl again after xdotool activation
                if command -v wmctrl >/dev/null 2>&1; then
                    if wmctrl -i -r "$win_id" -b remove,above 2>/dev/null; then
                        log_monitor "Successfully removed 'above' after xdotool activation"
                        return 0
                    fi
                fi
            fi
        fi
        
        retry_count=$((retry_count + 1))
        
        # X11 sync between retries
        sync_x11
        sleep 0.2
    done
    
    log_monitor "WARNING: Failed to remove 'above' flag after $max_retries attempts"
    return 1
}

log_monitor "Starting enhanced window monitor for PID $ENGINE_PID (Flatpak: $IN_FLATPAK)"

attempt=0
max_attempts=600  # 5 minutes at 0.5 second intervals
window_found=false

while [[ $attempt -lt $max_attempts ]]; do
    # Check if engine process is still alive
    if ! kill -0 "$ENGINE_PID" 2>/dev/null; then
        log_monitor "Engine PID $ENGINE_PID died, exiting monitor"
        exit 0
    fi
    
    attempt=$((attempt + 1))
    
    if [[ "$REMOVE_ABOVE" == "true" ]]; then
        # Try to find window by process ID
        if ! $window_found; then
            if win_id=$(get_window_for_pid "$ENGINE_PID"); then
                log_monitor "Found window $win_id for PID $ENGINE_PID"
                window_found=true
                
                # Apply flags immediately
                apply_window_flags "$win_id" &
            fi
        fi
        
        # Also try generic search (in case multiple windows or PID tracking fails)
        if command -v wmctrl >/dev/null 2>&1; then
            # Launch async window fixing in background
            {
                timeout 2 bash -c '
                    wmctrl -lx 2>/dev/null | grep -iE "linux-wallpaperengine|wallpaperengine|steam_app_431960" | while read -r line; do
                        win=$(echo "$line" | awk "{print \$1}")
                        if [[ -n "$win" ]]; then
                            timeout 0.5 wmctrl -i -r "$win" -b remove,above 2>/dev/null || true
                            timeout 0.5 wmctrl -i -r "$win" -b add,skip_pager 2>/dev/null || true
                            timeout 0.5 wmctrl -i -r "$win" -b add,below 2>/dev/null || true
                        fi
                    done
                ' 2>/dev/null || true
            } &
        fi
        
        # Log periodic status (every 60 attempts = 30 seconds)
        if [[ $((attempt % 60)) -eq 0 ]]; then
            log_monitor "Monitor running - attempt $attempt/$max_attempts (window_found: $window_found)"
        fi
    fi
    
    # Sleep for 0.5 seconds before next check
    sleep 0.5
done

log_monitor "Monitor exceeded max attempts ($max_attempts), exiting"
exit 0
