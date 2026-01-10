#!/bin/bash
# async-window-fixer.sh
# Ultra-aggressive async window flag manipulation
# Launches window manipulation attempts in completely non-blocking way
# Uses timeouts and background spawning to prevent Flatpak blocking
#
# Usage: async-window-fixer.sh <pid> <method> [app_id]
# Methods: direct, flatpak-enter, both
#
# This script is meant to be launched and immediately return
# All work happens in background subprocesses

set -euo pipefail

ENGINE_PID="${1:-}"
METHOD="${2:-both}"
FLATPAK_APP_ID="${3:-}"

if [[ -z "$ENGINE_PID" ]]; then
    exit 1
fi

# Try direct wmctrl in completely non-blocking way
try_direct_wmctrl() {
    local pid=$1
    # Timeout after 2 seconds, run in background, suppress all output
    timeout 2 wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}' | while read -r win; do
        timeout 1 wmctrl -i -r "$win" -b remove,above 2>/dev/null || true &
        timeout 1 wmctrl -i -r "$win" -b add,skip_pager 2>/dev/null || true &
        timeout 1 wmctrl -i -r "$win" -b add,below 2>/dev/null || true &
    done &
}

# Try flatpak-enter in completely non-blocking way
try_flatpak_enter() {
    local pid=$1
    local app_id=$2
    if [[ -z "$app_id" ]] || ! command -v flatpak-enter >/dev/null 2>&1; then
        return
    fi
    # Timeout after 3 seconds, run in background, suppress all output
    timeout 3 flatpak-enter "$pid" wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}' | while read -r win; do
        timeout 1 flatpak-enter "$pid" wmctrl -i -r "$win" -b remove,above 2>/dev/null || true &
        timeout 1 flatpak-enter "$pid" wmctrl -i -r "$win" -b add,skip_pager 2>/dev/null || true &
        timeout 1 flatpak-enter "$pid" wmctrl -i -r "$win" -b add,below 2>/dev/null || true &
    done &
}

case "$METHOD" in
    direct)
        try_direct_wmctrl "$ENGINE_PID" &
        ;;
    flatpak-enter)
        try_flatpak_enter "$ENGINE_PID" "$FLATPAK_APP_ID" &
        ;;
    both)
        try_direct_wmctrl "$ENGINE_PID" &
        sleep 0.1
        try_flatpak_enter "$ENGINE_PID" "$FLATPAK_APP_ID" &
        ;;
esac

# Return immediately, don't wait for background jobs
exit 0
