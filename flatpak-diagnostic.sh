#!/bin/bash
# flatpak-diagnostic.sh
# Diagnostic script to verify Flatpak environment and window manipulation capabilities
# Useful for debugging why --above flag doesn't work in Flatpak

set -euo pipefail

echo "=========================================="
echo "Flatpak Diagnostic Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FLATPAK_APP="com.github.mauefrod.LWEExpandedFeaturesGUI"
ISSUES=0
WARNINGS=0

# Helper functions
success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    ISSUES=$((ISSUES + 1))
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Flatpak is installed
echo "1. Checking Flatpak installation..."
if command -v flatpak >/dev/null 2>&1; then
    success "Flatpak is installed"
    info "Version: $(flatpak --version)"
else
    error "Flatpak is not installed"
    exit 1
fi
echo ""

# Check if app is installed
echo "2. Checking if LWE GUI is installed in Flatpak..."
if flatpak list --app | grep -q "$FLATPAK_APP"; then
    success "Application is installed: $FLATPAK_APP"
else
    warning "Application not found. Install with: flatpak-builder --user --install build-dir flatpak/com.github.mauefrod.LWEExpandedFeaturesGUI.yml"
fi
echo ""

# Test Flatpak environment
echo "3. Testing Flatpak environment variables..."
{
    echo "Checking DISPLAY..."
    DISPLAY_VAL=$(flatpak run --command=bash "$FLATPAK_APP" -c 'echo $DISPLAY' 2>&1 || echo "ERROR")
    if [[ "$DISPLAY_VAL" != "ERROR" ]] && [[ ! -z "$DISPLAY_VAL" ]]; then
        success "DISPLAY is set: $DISPLAY_VAL"
    else
        error "DISPLAY not set in Flatpak: $DISPLAY_VAL"
    fi
    
    echo "Checking XAUTHORITY..."
    XAUTH_VAL=$(flatpak run --command=bash "$FLATPAK_APP" -c 'echo $XAUTHORITY' 2>&1 || echo "ERROR")
    if [[ "$XAUTH_VAL" != "ERROR" ]]; then
        success "XAUTHORITY is set: $XAUTH_VAL"
    else
        warning "XAUTHORITY not set or has restricted value"
    fi
} 2>/dev/null || error "Could not query Flatpak environment"
echo ""

# Test wmctrl availability
echo "4. Checking wmctrl in Flatpak..."
{
    WMCTRL_PATH=$(flatpak run --command=which "$FLATPAK_APP" wmctrl 2>&1 || echo "NOT_FOUND")
    if [[ "$WMCTRL_PATH" != "NOT_FOUND" ]]; then
        success "wmctrl found at: $WMCTRL_PATH"
        
        # Test wmctrl functionality
        WMCTRL_TEST=$(flatpak run --command=bash "$FLATPAK_APP" -c 'wmctrl -lx 2>&1 | head -1' 2>/dev/null || echo "ERROR")
        if [[ "$WMCTRL_TEST" != "ERROR" ]]; then
            success "wmctrl is functional"
            info "Sample output: $WMCTRL_TEST"
        else
            error "wmctrl is installed but not functional"
        fi
    else
        error "wmctrl not found in Flatpak"
    fi
} 2>/dev/null || error "Could not test wmctrl"
echo ""

# Test xdotool availability
echo "5. Checking xdotool in Flatpak..."
{
    XDOTOOL_PATH=$(flatpak run --command=which "$FLATPAK_APP" xdotool 2>&1 || echo "NOT_FOUND")
    if [[ "$XDOTOOL_PATH" != "NOT_FOUND" ]]; then
        success "xdotool found at: $XDOTOOL_PATH"
        
        # Test xdotool functionality
        XDOTOOL_TEST=$(flatpak run --command=bash "$FLATPAK_APP" -c 'xdotool getactivewindow 2>&1' 2>/dev/null || echo "ERROR")
        if [[ "$XDOTOOL_TEST" != "ERROR" ]]; then
            success "xdotool is functional"
            info "Active window ID: $XDOTOOL_TEST"
        else
            warning "xdotool found but might not be fully functional"
        fi
    else
        error "xdotool not found in Flatpak"
    fi
} 2>/dev/null || error "Could not test xdotool"
echo ""

# Check Flatpak permissions
echo "6. Checking Flatpak permissions..."
{
    # Get app metadata
    APP_DIR="$(flatpak info --show-location "$FLATPAK_APP" 2>/dev/null || echo 'NOT_FOUND')"
    
    if [[ "$APP_DIR" != "NOT_FOUND" ]]; then
        METADATA_FILE="$APP_DIR/metadata"
        
        if [[ -f "$METADATA_FILE" ]]; then
            echo "Checking key permissions..."
            
            # Check X11 socket
            if grep -q "socket=x11" "$METADATA_FILE"; then
                success "X11 socket permission present"
            else
                error "X11 socket permission missing"
            fi
            
            # Check IPC
            if grep -q "share=ipc" "$METADATA_FILE"; then
                success "IPC sharing permission present"
            else
                warning "IPC sharing permission might improve X11 performance"
            fi
            
            # Check home filesystem access
            if grep -q "filesystem=home" "$METADATA_FILE"; then
                success "Home filesystem access permission present"
            else
                error "Home filesystem access permission missing"
            fi
            
            # Check DBus permissions
            if grep -q "talk-name=org.freedesktop.DBus" "$METADATA_FILE"; then
                success "DBus talk permission present"
            else
                warning "DBus talk permission might improve window detection"
            fi
        else
            warning "Could not read metadata file: $METADATA_FILE"
        fi
    else
        warning "Could not locate app directory for metadata check"
    fi
} 2>/dev/null || warning "Could not check Flatpak permissions"
echo ""

# Test X11 socket access
echo "7. Testing X11 socket access..."
{
    X11_SOCKET=$(flatpak run --command=bash "$FLATPAK_APP" -c 'ls -la /tmp/.X11-unix/ 2>&1 | head -3' 2>/dev/null || echo "ERROR")
    if [[ "$X11_SOCKET" != "ERROR" ]]; then
        success "X11 socket directory accessible"
        info "Content:\n$X11_SOCKET"
    else
        error "Cannot access X11 socket directory"
    fi
} 2>/dev/null || error "Could not test X11 socket"
echo ""

# Test window manipulation capabilities
echo "8. Testing window manipulation (requires running wallpaper engine)..."
info "This test requires the linux-wallpaperengine to be running"
{
    WALLPAPER_WINDOWS=$(flatpak run --command=bash "$FLATPAK_APP" -c 'wmctrl -lx 2>/dev/null | grep -i "wallpaper\|steam" | wc -l' 2>/dev/null || echo "0")
    if [[ "$WALLPAPER_WINDOWS" -gt 0 ]]; then
        success "Found $WALLPAPER_WINDOWS wallpaper-related window(s)"
        
        # Try to get window details
        WINDOW_INFO=$(flatpak run --command=bash "$FLATPAK_APP" -c 'wmctrl -lx 2>/dev/null | grep -i "wallpaper\|steam"' 2>/dev/null || echo "")
        info "Window details:\n$WINDOW_INFO"
    else
        warning "No wallpaper windows found (engine might not be running)"
    fi
} 2>/dev/null || warning "Could not test window manipulation"
echo ""

# Check backend script
echo "9. Checking backend scripts in Flatpak..."
{
    MAIN_SH=$(flatpak run --command=bash "$FLATPAK_APP" -c '[ -f /app/share/lwe-gui/source/core/main.sh ] && echo "FOUND" || echo "NOT_FOUND"' 2>/dev/null || echo "ERROR")
    if [[ "$MAIN_SH" == "FOUND" ]]; then
        success "main.sh found in Flatpak"
    else
        error "main.sh not found in Flatpak"
    fi
    
    WINDOW_MON=$(flatpak run --command=bash "$FLATPAK_APP" -c '[ -f /app/share/lwe-gui/source/core/window-monitor.sh ] && echo "FOUND" || echo "NOT_FOUND"' 2>/dev/null || echo "ERROR")
    if [[ "$WINDOW_MON" == "FOUND" ]]; then
        success "window-monitor.sh found in Flatpak"
    else
        error "window-monitor.sh not found in Flatpak"
    fi
} 2>/dev/null || error "Could not check backend scripts"
echo ""

# Check log files
echo "10. Checking application logs..."
{
    LOG_FILE="$HOME/.local/share/linux-wallpaper-engine-features/logs.txt"
    if [[ -f "$LOG_FILE" ]]; then
        success "Log file found: $LOG_FILE"
        info "Last 10 lines:"
        tail -10 "$LOG_FILE" | sed 's/^/  /'
    else
        warning "Log file not found yet (first run?)"
    fi
} 2>/dev/null || warning "Could not access log files"
echo ""

# Summary
echo "=========================================="
echo "Diagnostic Summary"
echo "=========================================="
echo -e "${GREEN}Issues found: $ISSUES${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [[ $ISSUES -eq 0 ]]; then
    success "All critical checks passed!"
    if [[ $WARNINGS -gt 0 ]]; then
        info "Review $WARNINGS warning(s) for better reliability"
    fi
else
    error "Fix $ISSUES critical issue(s) before using the --above flag"
fi

echo ""
echo "Recommendations:"
if [[ $ISSUES -gt 0 ]]; then
    echo "1. Rebuild Flatpak with updated manifest:"
    echo "   flatpak-builder --user --install --force-clean build-dir flatpak/com.github.mauefrod.LWEExpandedFeaturesGUI.yml"
    echo ""
fi

echo "2. Check if native installation works:"
echo "   ./install.sh && ./run.sh --above --set /path/to/wallpaper"
echo ""

echo "3. Review application logs:"
echo "   tail -f ~/.local/share/linux-wallpaper-engine-features/logs.txt"
echo ""

echo "4. For more details, see:"
echo "   FLATPAK_ABOVE_FLAG_FIX.md"
echo ""

exit $ISSUES
