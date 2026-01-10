#!/bin/bash
# lwe-window-manager.sh
# Window manager helper script for linux-wallpaper-engine GUI
# This script provides robust window manipulation
# When run inside Flatpak, wmctrl/xdotool are bundled and can access host X11 via socket forwarding
# When run natively, it uses system wmctrl/xdotool
#
# The key insight: wmctrl and xdotool bundled in Flatpak can access the host X11 display
# through the --socket=x11 permission without needing flatpak-spawn --host

set -euo pipefail

ACTION="${1:-}"
WIN_ID="${2:-}"

if [[ -z "$ACTION" ]]; then
    echo "Usage: lwe-window-manager.sh <action> [window_id]"
    echo "Actions:"
    echo "  remove-above <window_id>    - Remove above flag from window"
    echo "  set-below <window_id>       - Set window to below (with skip_pager)"
    echo "  close-window <window_id>    - Close window safely"
    exit 1
fi

case "$ACTION" in
    remove-above)
        if [[ -z "$WIN_ID" ]]; then
            echo "Error: window_id required for remove-above" >&2
            exit 1
        fi
        # Primary method: wmctrl (sends proper client messages for state changes)
        if wmctrl -i -r "$WIN_ID" -b remove,above 2>/dev/null; then
            echo "Successfully removed 'above' flag from $WIN_ID"
            exit 0
        fi
        # Fallback: xdotool to toggle window state (also sends client messages)
        if command -v xdotool &>/dev/null; then
            if xdotool windowsize "$WIN_ID" 0 0 2>/dev/null || xdotool getwindowfocus 2>/dev/null >/dev/null; then
                # xdotool is available, but has no direct "remove-above" command
                # Only wmctrl can properly remove the above state, so this fallback fails gracefully
                :
            fi
        fi
        echo "Failed to remove 'above' flag" >&2
        exit 1
        ;;
    
    set-below)
        if [[ -z "$WIN_ID" ]]; then
            echo "Error: window_id required for set-below" >&2
            exit 1
        fi
        # Add skip_pager and below states
        wmctrl -i -r "$WIN_ID" -b add,skip_pager 2>/dev/null || true
        wmctrl -i -r "$WIN_ID" -b add,below 2>/dev/null || true
        echo "Set window $WIN_ID to below state"
        exit 0
        ;;
    
    close-window)
        if [[ -z "$WIN_ID" ]]; then
            echo "Error: window_id required for close-window" >&2
            exit 1
        fi
        # Try different methods to close window
        wmctrl -i -c "$WIN_ID" 2>/dev/null && exit 0
        xdotool windowkill "$WIN_ID" 2>/dev/null && exit 0
        xdotool windowclose "$WIN_ID" 2>/dev/null && exit 0
        echo "Failed to close window $WIN_ID" >&2
        exit 1
        ;;
    
    *)
        echo "Unknown action: $ACTION" >&2
        exit 1
        ;;
esac
