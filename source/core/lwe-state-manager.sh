#!/bin/bash
# lwe-state-manager.sh
# Helper script to manage engine state for Flatpak compatibility
# This allows better process tracking even when wmctrl/xdotool are unavailable

set -euo pipefail

# Configuration
STATE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/linux-wallpaper-engine-features"
ENGINE_STATE="$STATE_DIR/engine.state"
ENGINES_RUNNING="$STATE_DIR/engines_running"

# Ensure state directory exists
mkdir -p "$STATE_DIR"

# Initialize empty state if missing
init_state() {
    if [[ ! -f "$ENGINE_STATE" ]]; then
        cat > "$ENGINE_STATE" <<EOF
{
  "last_pid": null,
  "last_windows": [],
  "last_wallpaper": null,
  "last_execution": null,
  "in_flatpak": $([ -f /.flatpak-info ] && echo "true" || echo "false")
}
EOF
        echo "Initialized state file: $ENGINE_STATE"
    fi
}

# Escape string for JSON (basic: escape backslashes and quotes)
json_escape() {
    local str="$1"
    str="${str//\\/\\\\}"  # Escape backslashes first
    str="${str//\"/\\\"}"  # Escape double quotes
    printf '%s' "$str"
}

# Save current engine state
save_state() {
    local pid="$1"
    local windows="${2:-}"
    local wallpaper="${3:-}"
    
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local escaped_wallpaper
    escaped_wallpaper=$(json_escape "$wallpaper")
    
    # Simple JSON write (bash-only, no jq dependency)
    cat > "$ENGINE_STATE" <<EOF
{
  "last_pid": $pid,
  "last_windows": [$(printf '"%s"' "${windows:-}")],
  "last_wallpaper": "$escaped_wallpaper",
  "last_execution": "$timestamp",
  "in_flatpak": $([ -f /.flatpak-info ] && echo "true" || echo "false")
}
EOF
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] State saved: PID=$pid, Windows=${windows:-none}"
}

# Get last engine PID
get_last_pid() {
    init_state
    
    # Simple grep to extract PID (works without jq)
    grep -o '"last_pid": [0-9]*' "$ENGINE_STATE" | grep -o '[0-9]*' || echo ""
}

# Get last engine windows
get_last_windows() {
    init_state
    
    if grep -q '"last_windows": \[\]' "$ENGINE_STATE"; then
        echo ""
    else
        # Extract window IDs (simple regex, assumes hex format 0xNNNNNNNN)
        grep -o '0x[0-9a-f]*' "$ENGINE_STATE" || true
    fi
}

# Check if a process is still running
is_running() {
    local pid="$1"
    if [[ -z "$pid" ]]; then
        return 1
    fi
    kill -0 "$pid" 2>/dev/null || return 1
}

# Kill engine by PID (with fallback to process name)
kill_engine() {
    local pid="${1:-}"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Killing engine (PID: ${pid:-unknown})"
    
    if [[ -n "$pid" ]] && is_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || true
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Killed PID $pid"
    fi
    
    # Fallback: kill by process name
    pkill -9 -f linux-wallpaperengine 2>/dev/null || true
    
    # Clear state
    save_state "null" "" ""
}

# Monitor and track engines
track_engine() {
    local pid="$1"
    local wallpaper="${2:-}"
    
    # Save state
    save_state "$pid" "" "$wallpaper"
    
    # Optionally add to running engines list
    echo "$pid:$wallpaper:$(date +%s)" >> "$ENGINES_RUNNING"
    
    # Cleanup old entries (keep only last 100)
    if [[ $(wc -l < "$ENGINES_RUNNING") -gt 100 ]]; then
        tail -100 "$ENGINES_RUNNING" > "$ENGINES_RUNNING.tmp"
        mv "$ENGINES_RUNNING.tmp" "$ENGINES_RUNNING"
    fi
}

# Print state info (for debugging)
show_state() {
    echo "=== LWE Engine State ==="
    echo "State File: $ENGINE_STATE"
    
    if [[ -f "$ENGINE_STATE" ]]; then
        cat "$ENGINE_STATE"
    else
        echo "No state file found"
    fi
    
    echo ""
    echo "Last PID: $(get_last_pid)"
    echo "Last Windows: $(get_last_windows)"
    
    if [[ -f "$ENGINES_RUNNING" ]]; then
        echo ""
        echo "Recent Engines:"
        tail -10 "$ENGINES_RUNNING"
    fi
}

# Cleanup old state files
cleanup() {
    local max_age=604800  # 7 days in seconds
    local now=$(date +%s)
    
    if [[ -f "$ENGINE_STATE" ]]; then
        local file_age=$((now - $(stat -f%m "$ENGINE_STATE" 2>/dev/null || stat -c%Y "$ENGINE_STATE" 2>/dev/null || echo 0)))
        if [[ $file_age -gt $max_age ]]; then
            rm -f "$ENGINE_STATE"
            echo "Cleaned up old state file"
        fi
    fi
    
    if [[ -f "$ENGINES_RUNNING" ]]; then
        # Keep only last 50 entries
        if [[ $(wc -l < "$ENGINES_RUNNING") -gt 50 ]]; then
            tail -50 "$ENGINES_RUNNING" > "$ENGINES_RUNNING.tmp"
            mv "$ENGINES_RUNNING.tmp" "$ENGINES_RUNNING"
        fi
    fi
}

# Main command handling
case "${1:-help}" in
    init)
        init_state
        ;;
    save)
        save_state "$2" "${3:-}" "${4:-}"
        ;;
    get-pid)
        get_last_pid
        ;;
    get-windows)
        get_last_windows
        ;;
    is-running)
        is_running "$2" && echo "yes" || echo "no"
        ;;
    kill)
        kill_engine "${2:-}"
        ;;
    track)
        track_engine "$2" "${3:-}"
        ;;
    show)
        show_state
        ;;
    cleanup)
        cleanup
        ;;
    help|*)
        cat <<EOF
LWE State Manager - Manage linux-wallpaperengine state for Flatpak

Usage: $0 COMMAND [ARGS]

Commands:
    init                 Initialize state file
    save PID WINDOWS WP   Save engine state
    get-pid              Get last engine PID
    get-windows          Get last engine windows
    is-running PID       Check if PID is running
    kill [PID]          Kill engine (by PID or process name)
    track PID [WP]      Track new engine execution
    show                 Display current state
    cleanup              Clean up old state files
    help                 Show this help message

Environment:
    STATE_DIR: $STATE_DIR
    ENGINE_STATE: $ENGINE_STATE
    ENGINES_RUNNING: $ENGINES_RUNNING

Example:
    $0 track 12345 /path/to/wallpaper
    $0 show
    $0 kill

EOF
        ;;
esac
