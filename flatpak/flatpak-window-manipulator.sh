#!/bin/bash
# flatpak-window-manipulator.sh
# Access Flatpak sandbox namespace to manipulate windows
# This script enters the Flatpak sandbox and applies window flags using wmctrl from inside
#
# Usage: flatpak-window-manipulator.sh <app_id> <pid> <action> [window_id]
# Examples:
#   flatpak-window-manipulator.sh com.github.mauefrod.LWEExpandedFeaturesGUI 1234 remove-above
#   flatpak-window-manipulator.sh com.github.mauefrod.LWEExpandedFeaturesGUI 1234 close-window 0x1a00001

set -euo pipefail

APP_ID="${1:-}"
TARGET_PID="${2:-}"
ACTION="${3:-}"
WINDOW_ID="${4:-}"

if [[ -z "$APP_ID" ]] || [[ -z "$TARGET_PID" ]] || [[ -z "$ACTION" ]]; then
    echo "Usage: $0 <app_id> <pid> <action> [window_id]"
    echo "Actions: remove-above, close-window, set-below"
    exit 1
fi

# Check if flatpak-enter is available
if ! command -v flatpak-enter >/dev/null 2>&1; then
    echo "Error: flatpak-enter not found. Install flatpak to use this tool."
    exit 1
fi

case "$ACTION" in
    remove-above)
        # Find all wallpaper engine windows and remove above flag
        if ! flatpak-enter "$TARGET_PID" wmctrl -lx &>/dev/null; then
            exit 1
        fi
        
        # Get windows and remove above flag from each
        mapfile -t windows < <(flatpak-enter "$TARGET_PID" wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}' || true)
        
        for win in "${windows[@]:-}"; do
            if [[ -n "$win" ]]; then
                flatpak-enter "$TARGET_PID" wmctrl -i -r "$win" -b remove,above 2>/dev/null || true
                flatpak-enter "$TARGET_PID" wmctrl -i -r "$win" -b add,skip_pager 2>/dev/null || true
                flatpak-enter "$TARGET_PID" wmctrl -i -r "$win" -b add,below 2>/dev/null || true
                echo "Removed 'above' flag from window $win"
            fi
        done
        ;;
    
    close-window)
        if [[ -z "$WINDOW_ID" ]]; then
            echo "Error: window_id required for close-window"
            exit 1
        fi
        flatpak-enter "$TARGET_PID" wmctrl -i -c "$WINDOW_ID" 2>/dev/null && echo "Closed window $WINDOW_ID" || exit 1
        ;;
    
    set-below)
        if [[ -z "$WINDOW_ID" ]]; then
            echo "Error: window_id required for set-below"
            exit 1
        fi
        flatpak-enter "$TARGET_PID" wmctrl -i -r "$WINDOW_ID" -b add,below 2>/dev/null && echo "Set window $WINDOW_ID to below" || exit 1
        ;;
    
    *)
        echo "Unknown action: $ACTION"
        exit 1
        ;;
esac
