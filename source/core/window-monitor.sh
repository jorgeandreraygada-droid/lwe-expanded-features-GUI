#!/bin/bash
# window-monitor.sh
# Background daemon to monitor and manipulate LWE windows
# This script runs in the background and periodically attempts to apply window flags
# Uses two strategies:
#  1. Direct wmctrl (if running native or has X11 access)
#  2. flatpak-enter to access sandbox namespace (if running in Flatpak)
#
# Usage: window-monitor.sh <pid> <remove_above> [log_file] [app_id]
# Args:
#   pid: PID of the engine process to monitor
#   remove_above: "true" or "false" - whether to remove above flag
#   log_file: optional log file path
#   app_id: optional Flatpak app ID (e.g., com.github.mauefrod.LWEExpandedFeaturesGUI)

set -euo pipefail

ENGINE_PID="${1:-}"
REMOVE_ABOVE="${2:-false}"
LOG_FILE="${3:-}"
FLATPAK_APP_ID="${4:-}"

# Exit if no PID provided
if [[ -z "$ENGINE_PID" ]]; then
    exit 1
fi

# Logging function
log_monitor() {
    if [[ -n "$LOG_FILE" ]] && [[ -w "$LOG_FILE" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MONITOR-$$] $*" >> "$LOG_FILE"
    fi
}

log_monitor "Starting window monitor for PID $ENGINE_PID (remove_above=$REMOVE_ABOVE, app_id=${FLATPAK_APP_ID:-none})"

# Determine if we can use flatpak-enter
use_flatpak_enter=false
if [[ -n "$FLATPAK_APP_ID" ]] && command -v flatpak-enter >/dev/null 2>&1; then
    use_flatpak_enter=true
    log_monitor "Will use flatpak-enter for window manipulation"
fi

# Counter for retry attempts
attempt=0
max_attempts=600  # 5 minutes with 0.5s intervals
success_count=0

while [[ $attempt -lt $max_attempts ]]; do
    # Check if engine process is still alive
    if ! kill -0 "$ENGINE_PID" 2>/dev/null; then
        log_monitor "Engine PID $ENGINE_PID is no longer running, exiting monitor after $success_count successful flag applications"
        exit 0
    fi
    
    attempt=$((attempt + 1))
    
    # Try to find and manipulate windows
    if [[ "$use_flatpak_enter" == "true" ]]; then
        # Use flatpak-enter to access sandbox namespace
        if local -a windows; mapfile -t windows < <(flatpak-enter "$ENGINE_PID" wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}' || true); then
            if [[ ${#windows[@]} -gt 0 ]]; then
                for win in "${windows[@]}"; do
                    if [[ -n "$win" ]]; then
                        if [[ "$REMOVE_ABOVE" == "true" ]]; then
                            # Remove above flag and add below
                            if flatpak-enter "$ENGINE_PID" wmctrl -i -r "$win" -b remove,above 2>/dev/null; then
                                flatpak-enter "$ENGINE_PID" wmctrl -i -r "$win" -b add,skip_pager 2>/dev/null || true
                                flatpak-enter "$ENGINE_PID" wmctrl -i -r "$win" -b add,below 2>/dev/null || true
                                success_count=$((success_count + 1))
                                if [[ $((attempt % 10)) -eq 0 ]] || [[ $success_count -eq 1 ]]; then
                                    log_monitor "Applied window flags to window $win via flatpak-enter (success #$success_count, attempt $attempt)"
                                fi
                            fi
                        fi
                    fi
                done
            fi
        fi
    else
        # Use direct wmctrl (native or X11 socket access)
        if command -v wmctrl >/dev/null 2>&1; then
            if local -a windows; mapfile -t windows < <(wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}' || true); then
                if [[ ${#windows[@]} -gt 0 ]]; then
                    for win in "${windows[@]}"; do
                        if [[ -n "$win" ]]; then
                            if [[ "$REMOVE_ABOVE" == "true" ]]; then
                                # Remove above flag and add below
                                if wmctrl -i -r "$win" -b remove,above 2>/dev/null; then
                                    wmctrl -i -r "$win" -b add,skip_pager 2>/dev/null || true
                                    wmctrl -i -r "$win" -b add,below 2>/dev/null || true
                                    success_count=$((success_count + 1))
                                    if [[ $((attempt % 10)) -eq 0 ]] || [[ $success_count -eq 1 ]]; then
                                        log_monitor "Applied window flags to window $win directly (success #$success_count, attempt $attempt)"
                                    fi
                                fi
                            fi
                        fi
                    done
                fi
            fi
        fi
    fi
    
    # Sleep briefly before next attempt
    sleep 0.5
done

log_monitor "Monitor exceeded max attempts ($max_attempts), exiting after $success_count successful flag applications"
exit 0
