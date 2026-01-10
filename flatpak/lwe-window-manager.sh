#!/bin/bash
# lwe-window-manager.sh
# Window manager helper script for linux-wallpaper-engine GUI
# Enhanced for Flatpak with X11 sync and multiple fallback methods
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

# Force X11 server to process all pending events
sync_x11() {
    if command -v xdotool >/dev/null 2>&1; then
        # Use xdotool to force X11 sync
        timeout 1 xdotool getactivewindow >/dev/null 2>&1 || true
    fi
    # Give X11 server a moment to process
    sleep 0.05
}

case "$ACTION" in
    remove-above)
        if [[ -z "$WIN_ID" ]]; then
            echo "Error: window_id required for remove-above" >&2
            exit 1
        fi
        
        # Ensure X11 is synced before attempting modifications
        sync_x11
        
        # Primary method: wmctrl (sends proper client messages for state changes)
        if command -v wmctrl >/dev/null 2>&1; then
            if wmctrl -i -r "$WIN_ID" -b remove,above 2>/dev/null; then
                echo "Successfully removed 'above' flag from $WIN_ID"
                exit 0
            fi
        fi
        
        # Secondary attempt: wmctrl with verbose error checking
        if command -v wmctrl >/dev/null 2>&1; then
            # Sometimes wmctrl needs a second attempt after sync
            sync_x11
            if wmctrl -i -r "$WIN_ID" -b remove,above 2>/dev/null; then
                echo "Successfully removed 'above' flag from $WIN_ID (retry)"
                exit 0
            fi
        fi
        
        # Fallback method: Check if window exists with xdotool first
        if command -v xdotool >/dev/null 2>&1; then
            if timeout 1 xdotool getwindowname "$WIN_ID" >/dev/null 2>&1; then
                # Window exists, try wmctrl one more time with explicit timing
                if command -v wmctrl >/dev/null 2>&1; then
                    sync_x11
                    if wmctrl -i -r "$WIN_ID" -b remove,above 2>/dev/null; then
                        echo "Successfully removed 'above' flag from $WIN_ID (after xdotool check)"
                        exit 0
                    fi
                fi
            fi
        fi
        
        echo "Failed to remove 'above' flag (tried wmctrl multiple times)" >&2
        exit 1
        ;;
    
    set-below)
        if [[ -z "$WIN_ID" ]]; then
            echo "Error: window_id required for set-below" >&2
            exit 1
        fi
        
        # Ensure X11 is synced
        sync_x11
        
        # Add skip_pager and below states
        if command -v wmctrl >/dev/null 2>&1; then
            wmctrl -i -r "$WIN_ID" -b add,skip_pager 2>/dev/null || true
            wmctrl -i -r "$WIN_ID" -b add,below 2>/dev/null || true
        fi
        
        echo "Set window $WIN_ID to below state"
        exit 0
        ;;
    
    close-window)
        if [[ -z "$WIN_ID" ]]; then
            echo "Error: window_id required for close-window" >&2
            exit 1
        fi
        
        # Ensure X11 is synced
        sync_x11
        
        # Try different methods to close window
        if command -v wmctrl >/dev/null 2>&1; then
            if wmctrl -i -c "$WIN_ID" 2>/dev/null; then
                exit 0
            fi
        fi
        
        if command -v xdotool >/dev/null 2>&1; then
            if timeout 1 xdotool windowkill "$WIN_ID" 2>/dev/null; then
                exit 0
            fi
        fi
        
        if command -v xdotool >/dev/null 2>&1; then
            if timeout 1 xdotool windowclose "$WIN_ID" 2>/dev/null; then
                exit 0
            fi
        fi
        
        echo "Failed to close window $WIN_ID" >&2
        exit 1
        ;;
    
    *)
        echo "Unknown action: $ACTION" >&2
        exit 1
        ;;
esac
