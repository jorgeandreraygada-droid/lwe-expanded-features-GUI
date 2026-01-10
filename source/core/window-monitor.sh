#!/bin/bash
# window-monitor.sh
# Background daemon to monitor and manipulate LWE windows
# ULTRA-ASYNC MODE: Launches all window manipulation attempts in parallel non-blocking subprocesses
# Never waits for wmctrl to complete
# Uses timeouts to prevent Flatpak from blocking the monitor itself
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

# Non-blocking logging
log_monitor() {
    if [[ -n "$LOG_FILE" ]] && [[ -w "$LOG_FILE" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MONITOR-$$] $*" >> "$LOG_FILE" &
    fi
}

log_monitor "Starting ultra-async window monitor for PID $ENGINE_PID"

attempt=0
max_attempts=600  # 5 minutes

while [[ $attempt -lt $max_attempts ]]; do
    # Check if engine process is still alive
    if ! kill -0 "$ENGINE_PID" 2>/dev/null; then
        log_monitor "Engine PID $ENGINE_PID died, exiting monitor"
        exit 0
    fi
    
    attempt=$((attempt + 1))
    
    if [[ "$REMOVE_ABOVE" == "true" ]]; then
        # Launch async window fixing in background, don't wait for it
        {
            # Try direct wmctrl (non-blocking)
            # This works because Flatpak has X11 socket forwarding
            if command -v wmctrl >/dev/null 2>&1; then
                timeout 1 bash -c 'wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk "{print \$1}" | while read -r win; do
                    timeout 0.5 wmctrl -i -r "$win" -b remove,above 2>/dev/null &
                    timeout 0.5 wmctrl -i -r "$win" -b add,skip_pager 2>/dev/null &
                    timeout 0.5 wmctrl -i -r "$win" -b add,below 2>/dev/null &
                done
                wait' 2>/dev/null || true
            fi
        } &
        
        # Don't wait for the background job - let it run in parallel
        async_pid=$!
        if [[ $((attempt % 60)) -eq 0 ]]; then
            log_monitor "Launched async window fix attempt (bg PID: $async_pid, attempt $attempt)"
        fi
    fi
    
    # Sleep for 0.5 seconds before next check
    # Monitor itself is never blocked
    sleep 0.5
done

log_monitor "Monitor exceeded max attempts, exiting"
exit 0
