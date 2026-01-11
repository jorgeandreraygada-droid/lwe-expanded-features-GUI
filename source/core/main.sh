#!/bin/bash
set -euo pipefail

# Support both Flatpak and native installations
DATA_DIR="${LWE_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/linux-wallpaper-engine-features}"
CONFIG_DIR="${LWE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/linux-wallpaper-engine-features}"

LOG_FILE="$DATA_DIR/logs.txt"
PID_FILE="$DATA_DIR/loop.pid"
ENGINE_STATE_FILE="$DATA_DIR/engine_state.json"
PREV_WINDOWS_FILE="$DATA_DIR/prev_windows.txt"

# Ensure directories exist
mkdir -p "$DATA_DIR" "$CONFIG_DIR"

# Detectar si estamos en Flatpak
if [ -f /.flatpak-info ]; then
    IN_FLATPAK=true
    # Get Flatpak app ID from environment or metadata
    FLATPAK_APP_ID="${FLATPAK_ID:-com.github.mauefrod.LWEExpandedFeaturesGUI}"
    # Inside Flatpak, wmctrl and xdotool are available locally (bundled in the Flatpak)
    # They can access the host's X11 through the X11 socket forwarding
    # NO need for flatpak-spawn --host; use local tools instead
    wmctrl() { command wmctrl "$@"; }
    xdotool() { command xdotool "$@"; }
    # Window manager script for robust window operations
    WINDOW_MANAGER="/app/bin/lwe-window-manager.sh"
    run_window_manager() { "$WINDOW_MANAGER" "$@"; }
else
    IN_FLATPAK=false
    FLATPAK_APP_ID=""
    WINDOW_MANAGER="/usr/local/bin/lwe-window-manager.sh"
    run_window_manager() { "$WINDOW_MANAGER" "$@"; }
fi

# Diagnostic function to test if wmctrl works
test_wmctrl() {
    if wmctrl -lx &>/dev/null; then
        return 0
    else
        # More detailed diagnostics - capture actual error
        local wmctrl_error
        wmctrl_error=$(wmctrl -lx 2>&1 || true)
        if [[ -n "$wmctrl_error" ]]; then
            log "DEBUG: wmctrl error output: $wmctrl_error"
        else
            log "DEBUG: wmctrl returned empty output (no windows or permission denied)"
        fi
        
        # Check if flatpak-spawn is available
        if [[ "$IN_FLATPAK" == "true" ]]; then
            if command -v flatpak-spawn >/dev/null 2>&1; then
                log "DEBUG: flatpak-spawn is available in PATH"
                # Try calling it directly to see if it works
                local spawn_test
                spawn_test=$(flatpak-spawn --host echo "OK" 2>&1 || true)
                if [[ "$spawn_test" == "OK" ]]; then
                    log "DEBUG: flatpak-spawn --host is working"
                else
                    log "DEBUG: flatpak-spawn --host test failed: $spawn_test"
                fi
            else
                log "DEBUG: flatpak-spawn NOT found in PATH"
            fi
        fi
        return 1
    fi
}

POOL=()
ENGINE=""  # Will be detected at startup
ENGINE_ARGS=()
SOUND_ARGS=()
REMOVE_ABOVE="false"
COMMAND=""
DELAY=""
ACTIVE_WIN=""

# log writes a timestamped message (YYYY-MM-DD HH:MM:SS) composed from its arguments and appends it to the file specified by LOG_FILE.
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg" >> "$LOG_FILE"
}

log "==================== NEW EXECUTION ===================="
log "Running in Flatpak: $IN_FLATPAK"

###############################################
#  ENGINE DETECTION (ROBUST)
###############################################
detect_engine() {
    log "Starting engine detection..."
    
    # Strategy 1: Check PATH for common binary names
    for binary in linux-wallpaperengine wallpaperengine; do
        if command -v "$binary" >/dev/null 2>&1; then
            ENGINE="$binary"
            local engine_path
            engine_path=$(command -v "$binary")
            log "Engine binary detected in PATH: $engine_path"
            
            # Try to get version info
            local version_info
            version_info=$("$binary" --version 2>/dev/null || echo "unknown")
            log "Engine version: $version_info"
            return 0
        fi
    done
    
    # Strategy 2: Check common installation locations
    local -a common_locations=(
        "$HOME/.local/bin/linux-wallpaperengine"
        "/usr/local/bin/linux-wallpaperengine"
        "/usr/bin/linux-wallpaperengine"
        "./linux-wallpaperengine/build/linux-wallpaperengine"
        "./linux-wallpaperengine/linux-wallpaperengine"
    )
    
    for location in "${common_locations[@]}"; do
        if [[ -x "$location" ]]; then
            ENGINE="$location"
            log "Engine binary detected at: $location"
            
            # Expand to absolute path if relative
            if [[ "$location" == "./"* ]]; then
                ENGINE="$(cd "$(dirname "$location")" && pwd)/$(basename "$location")"
                log "Resolved to absolute path: $ENGINE"
            fi
            
            return 0
        fi
    done
    
    # Strategy 3: In Flatpak, try to use host's engine via flatpak-spawn
    if [[ "$IN_FLATPAK" == "true" ]]; then
        log "Flatpak environment detected, trying host system engine"
        
        if command -v flatpak-spawn >/dev/null 2>&1; then
            # Test if engine is available on host
            if flatpak-spawn --host which linux-wallpaperengine >/dev/null 2>&1; then
                ENGINE="flatpak-spawn --host linux-wallpaperengine"
                log "Engine found on host system (via flatpak-spawn)"
                return 0
            elif flatpak-spawn --host which wallpaperengine >/dev/null 2>&1; then
                ENGINE="flatpak-spawn --host wallpaperengine"
                log "Engine found on host system as 'wallpaperengine' (via flatpak-spawn)"
                return 0
            else
                log "Engine not found on host system"
            fi
        else
            log "flatpak-spawn not available, cannot access host system"
        fi
    fi
    
    # Engine not found anywhere
    log "ERROR: linux-wallpaperengine binary not found"
    log "Searched locations:"
    log "  - PATH (as linux-wallpaperengine, wallpaperengine)"
    log "  - $HOME/.local/bin/linux-wallpaperengine"
    log "  - /usr/local/bin/linux-wallpaperengine"
    log "  - /usr/bin/linux-wallpaperengine"
    log "  - ./linux-wallpaperengine/build/linux-wallpaperengine"
    if [[ "$IN_FLATPAK" == "true" ]]; then
        log "  - Host system (via flatpak-spawn)"
    fi
    
    return 1
}

# Detect engine at startup
if ! detect_engine; then
    log "CRITICAL: Cannot proceed without engine binary"
    echo "ERROR: linux-wallpaperengine not found in PATH or common locations" >&2
    echo "" >&2
    echo "Please install linux-wallpaperengine first:" >&2
    echo "  - From source: https://github.com/Acters/linux-wallpaperengine" >&2
    echo "  - Arch Linux (AUR): yay -S linux-wallpaperengine-git" >&2
    echo "" >&2
    echo "Or ensure it's in one of these locations:" >&2
    echo "  - System PATH (/usr/bin, /usr/local/bin, ~/.local/bin)" >&2
    echo "  - ./linux-wallpaperengine/build/linux-wallpaperengine" >&2
    exit 1
fi

log "Using engine: $ENGINE"

###############################################
#  FLATPAK WINDOW DETECTION HELPER
#  When running in Flatpak, wmctrl has limitations.
#  This function uses multiple strategies to find windows:
#  1. Try wmctrl directly (may fail in Flatpak sandbox)
#  2. Fall back to process PID tracking
#  3. Use state file as last resort
###############################################
get_engine_windows() {
    local -a windows=()
    
    # Strategy 1: Try wmctrl (works better on native, may fail in Flatpak)
    if wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" &>/dev/null; then
        mapfile -t windows < <(wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}' || true)
        if [[ ${#windows[@]} -gt 0 ]]; then
            log "Window detection (wmctrl): Found ${#windows[@]} window(s)"
            printf "%s\n" "${windows[@]}"
            return 0
        fi
    fi
    
    # Strategy 2: Check stored window IDs from previous execution
    if [[ -f "$PREV_WINDOWS_FILE" ]]; then
        log "Window detection (fallback): Using stored window IDs"
        cat "$PREV_WINDOWS_FILE" || true
        return 0
    fi
    
    log "Window detection: No previous windows found"
    return 0
}

save_engine_state() {
    local pid="$1"
    shift
    local -a windows=("$@")
    
    # Save PID for later reference
    echo "$pid" > "$ENGINE_STATE_FILE.pid"
    
    # Save windows for fallback detection (one-per-line)
    printf "%s\n" "${windows[@]}" > "$PREV_WINDOWS_FILE"
    
    log "Engine state saved (PID: $pid, windows: ${windows[*]:-none})"
}


###############################################
#  KILL ENGINE (robusto, no mata el nuevo)
###############################################
kill_previous_engine() {
    log "Killing previous engine instances"
    
    # Kill by process name (most reliable)
    pkill -f linux-wallpaperengine 2>/dev/null || true
    
    # Try to close windows if we can detect them (native + Flatpak with --host)
    local -a old_windows
    mapfile -t old_windows < <(get_engine_windows)
    
    if [[ ${#old_windows[@]} -gt 0 ]]; then
        for win in "${old_windows[@]}"; do
            log "Attempting to close window: $win"
            wmctrl -i -c "$win" 2>/dev/null || true
        done
    fi
    
    # Give the process time to die
    sleep 0.5
}


###############################################
#  STOP TOTAL (mata loops + engine)
###############################################
cmd_stop() {
    log "Stopping ALL wallpaper engine processes and loops"

    # First, try to close windows gracefully (if wmctrl works)
    local -a engine_windows=()
    mapfile -t engine_windows < <(get_engine_windows)
    
    # Close windows gracefully first (skip empty/none values)
    if [[ ${#engine_windows[@]} -gt 0 ]]; then
        for win in "${engine_windows[@]}"; do
            if [[ -n "$win" ]] && [[ "$win" != "none" ]]; then
                log "Attempting to close window: $win"
                if run_window_manager "close-window" "$win" &>/dev/null; then
                    log "Successfully closed window $win"
                else
                    # Fallback to direct wmctrl
                    wmctrl -i -c "$win" 2>/dev/null || true
                fi
            fi
        done
    else
        log "No windows to close (array empty)"
    fi
    
    sleep 1

    # Kill engine processes (aggressive approach)
    log "Force killing engine processes"
    pkill -9 -f linux-wallpaperengine 2>/dev/null || true
    
    # Kill loop process if exists
    if [[ -f "$PID_FILE" ]]; then
        local loop_pid
        loop_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$loop_pid" ]]; then
            log "Killing loop process with PID: $loop_pid"
            # Try TERM first, then KILL
            kill -TERM "$loop_pid" 2>/dev/null || true
            sleep 0.2
            if kill -0 "$loop_pid" 2>/dev/null; then
                log "Loop process still alive, using SIGKILL"
                kill -9 "$loop_pid" 2>/dev/null || true
            fi
            sleep 0.3
            # Verify it's dead
            if kill -0 "$loop_pid" 2>/dev/null; then
                log "ERROR: Loop process $loop_pid still alive after SIGKILL, this should not happen"
                # Last resort: pkill by exact PID
                pkill -9 -P "$loop_pid" 2>/dev/null || true
            else
                log "Loop process successfully killed"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Final cleanup: kill any remaining main.sh instances (the loop script)
    pkill -9 -f "bash.*main.sh" 2>/dev/null || true
    
    # Clear state files
    rm -f "$PREV_WINDOWS_FILE" "$ENGINE_STATE_FILE.pid" 2>/dev/null || true
    
    log "Stop command completed - all processes should be terminated"
}


###############################################
#  Esperar ventana del engine (excluyendo antiguas)
# wait_for_window waits for a new engine-related window that is not in the provided exclusion list and echoes its window ID.
# It accepts zero or more window IDs to ignore (exclude_windows). Searches wmctrl for windows matching
# "linux-wallpaperengine", "wallpaperengine", or "steam_app_431960" and returns the first ID not in the exclusions.
# If no new window is found within ~10 seconds, logs an error and echoes an empty string.
# 
# FLATPAK NOTE: If wmctrl fails completely (in strict sandboxes), this falls back to waiting by process existence
# and assumes the window was created successfully after a delay.
wait_for_window() {
    local -a exclude_windows=("$@")
    local win=""
    local wmctrl_works=true
    
    # Quick test: does wmctrl work?
    if ! test_wmctrl; then
        log "WARNING: wmctrl not working (possible Flatpak sandbox restriction)"
        log "DEBUG: Flatpak mode: $IN_FLATPAK | flatpak-spawn available: $(command -v flatpak-spawn >/dev/null 2>&1 && echo yes || echo no)"
        wmctrl_works=false
    else
        log "DEBUG: wmctrl is working correctly"
    fi
    
    for i in {1..200}; do
        local -a current_windows=()
        
        if [[ "$wmctrl_works" == "true" ]]; then
            mapfile -t current_windows < <(wmctrl -lx 2>/dev/null | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}' || true)
        else
            # Fallback: if wmctrl doesn't work, just wait a bit and assume window is ready
            # This is a workaround for strict Flatpak sandboxes
            if [[ $i -ge 20 ]]; then
                log "FLATPAK FALLBACK: Assuming window created after delay (wmctrl unavailable after $((i*50))ms)"
                echo ""
                return
            fi
            sleep 0.1
            continue
        fi
        
        # Buscar ventana que NO esté en la lista de exclusión
        for w in "${current_windows[@]}"; do
            local is_old=false
            for old_w in "${exclude_windows[@]}"; do
                if [[ "$w" == "$old_w" ]]; then
                    is_old=true
                    break
                fi
            done
            
            if [[ "$is_old" == "false" ]]; then
                log "New window detected: $w"
                echo "$w"
                return
            fi
        done

        sleep 0.05
    done

    log "ERROR: Could not find new engine window (timeout after ~10s)"
    echo ""
}


###############################################
#  Aplicar flags de ventana
# apply_window_flags removes the 'above' flag and adds 'skip_pager' and 'below' to the specified window ID, then restores focus to the previously active window if set.
apply_window_flags() {
    local win_id="$1"

    if [[ "$REMOVE_ABOVE" == "false" ]]; then
        log "Skipping window flag modifications"
        return
    fi

    log "Applying window flags to $win_id (Flatpak: $IN_FLATPAK)"
    
    # Use robust window manager script for better reliability
    if run_window_manager "remove-above" "$win_id" &>/dev/null; then
        log "Successfully removed 'above' flag via window manager"
    else
        log "WARNING: Window manager failed to remove 'above' flag, trying direct wmctrl"
        if wmctrl -i -r "$win_id" -b remove,above 2>/dev/null; then
            log "Successfully removed 'above' flag via wmctrl"
        else
            log "CRITICAL: Failed to remove 'above' flag via all methods"
        fi
    fi
    
    # Set below and skip_pager via window manager
    if run_window_manager "set-below" "$win_id" &>/dev/null; then
        log "Successfully set window to below state"
    else
        log "WARNING: Failed to set below state, trying direct wmctrl"
        wmctrl -i -r "$win_id" -b add,skip_pager 2>/dev/null || log "WARNING: Failed to add 'skip_pager'"
        wmctrl -i -r "$win_id" -b add,below 2>/dev/null || log "WARNING: Failed to add 'below'"
    fi

    if [[ -n "$ACTIVE_WIN" ]]; then
        log "Restoring focus to previous window: $ACTIVE_WIN"
        xdotool windowactivate "$ACTIVE_WIN" 2>/dev/null || log "WARNING: Failed to restore focus"
    fi
}


###############################################
#  Aplicar wallpaper (CON TRANSICIÓN SUAVE)
# apply_wallpaper launches the wallpaper engine for the given wallpaper path, waits for the newly created window, applies window flags (and optionally restores focus), and closes any previous engine windows while logging progress and errors.
#
# FLATPAK ADAPTATION: Enhanced detection fallback for sandboxed environments
apply_wallpaper() {
    local path="$1"

    log "Applying wallpaper: $path"

    # Guardamos las ventanas actuales del engine ANTES de lanzar el nuevo
    local old_windows=()
    mapfile -t old_windows < <(get_engine_windows)
    log "Old engine windows: ${old_windows[*]:-none}"

    ACTIVE_WIN=$(xdotool getactivewindow 2>/dev/null || echo "")
    log "Active window before launch: ${ACTIVE_WIN:-none}"

    # Construir comando completo con flags de sonido
    local -a full_args=("${ENGINE_ARGS[@]}")
    
    # Añadir flags de sonido si existen
    if [[ ${#SOUND_ARGS[@]} -gt 0 ]]; then
        log "Adding sound flags: ${SOUND_ARGS[*]}"
        full_args+=("${SOUND_ARGS[@]}")
    fi
    
    # Añadir el path del wallpaper al final
    full_args+=("$path")

    # Lanzamos el engine con todos los argumentos
    log "Executing: $ENGINE ${full_args[*]}"
    
    # Handle ENGINE commands that might contain spaces (like "flatpak-spawn --host linux-wallpaperengine")
    if [[ "$ENGINE" == *" "* ]]; then
        # ENGINE contains spaces, execute as shell command
        $ENGINE "${full_args[@]}" &
    else
        # ENGINE is a single binary path
        "$ENGINE" "${full_args[@]}" &
    fi
    
    local new_pid=$!
    log "Engine launched with PID $new_pid"
    
    # Start background monitor to continuously try to apply window flags
    # This is a workaround for Flatpak restrictions on wmctrl
    # Uses flatpak-enter if available to access sandbox namespace
    if [[ "$REMOVE_ABOVE" == "true" ]]; then
        local monitor_script
        monitor_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/window-monitor.sh"
        if [[ -f "$monitor_script" ]]; then
            log "Starting background window monitor (REMOVE_ABOVE=true, Flatpak=$IN_FLATPAK)"
            if [[ "$IN_FLATPAK" == "true" ]]; then
                # Pass Flatpak app ID so monitor can use flatpak-enter
                bash "$monitor_script" "$new_pid" "$REMOVE_ABOVE" "$LOG_FILE" "$FLATPAK_APP_ID" &
            else
                bash "$monitor_script" "$new_pid" "$REMOVE_ABOVE" "$LOG_FILE" &
            fi
            local monitor_pid=$!
            log "Window monitor started with PID $monitor_pid"
        else
            log "WARNING: window-monitor.sh not found at $monitor_script"
        fi
    fi

    # Esperamos a que la NUEVA ventana esté lista (excluyendo las antiguas)
    local win_id
    win_id=$(wait_for_window "${old_windows[@]}")

    if [[ -z "$win_id" ]]; then
        log "WARNING: No window found for new engine (may be hidden or in Flatpak sandbox)"
        # Store state for future reference even if we can't detect window
        save_engine_state "$new_pid" "${old_windows[@]:-none}"
        # In Flatpak, the process will still be running even if we can't detect the window
        log "Proceeding without window detection (process running with PID $new_pid)"
        return
    fi

    apply_window_flags "$win_id"
    
    # Save current windows for next invocation
    save_engine_state "$new_pid" "$win_id"

    log "New window ready, now killing old instances"
    if [[ ${#old_windows[@]} -gt 0 ]]; then
        for old_win in "${old_windows[@]}"; do
            if [[ "$old_win" != "$win_id" ]]; then
                log "Killing old window: $old_win"
                wmctrl -i -c "$old_win" 2>/dev/null || true
            else
                log "Skipping new window: $old_win (matches $win_id)"
            fi
        done
    else
        log "No old windows to close"
    fi
    
    log "Transition complete"
}


###############################################
#  RANDOM
###############################################
cmd_random() {
    local list=()

    if [[ ${#POOL[@]} -gt 0 ]]; then
        list=("${POOL[@]}")
        log "Using POOL for random selection (${#POOL[@]} items)"
    else
        if [[ -z "${WALLPAPERS_DIRECTORY:-}" ]]; then
            log "ERROR: WALLPAPERS_DIRECTORY is not set"
            return
        fi
        log "POOL empty, scanning directory: $WALLPAPERS_DIRECTORY"
        mapfile -t list < <(find "$WALLPAPERS_DIRECTORY" -mindepth 1 -maxdepth 1 -type d)
    fi

    if [[ ${#list[@]} -eq 0 ]]; then
        log "ERROR: No wallpapers found for random selection"
        return
    fi

    local id="${list[RANDOM % ${#list[@]}]}"
    log "Randomly selected: $id"
    apply_wallpaper "$id"
}


###############################################
#  SET
###############################################
cmd_set() {
    log "Setting wallpaper (set): $1"
    apply_wallpaper "$1"
}


###############################################
#  LIST
###############################################
cmd_list() {
    if [[ -z "${WALLPAPERS_DIRECTORY:-}" ]]; then
        log "ERROR: WALLPAPERS_DIRECTORY is not set for list"
        return
    fi
    log "Listing wallpapers in: $WALLPAPERS_DIRECTORY"
    mapfile -t WALLPAPERS_IDS < <(find "$WALLPAPERS_DIRECTORY" -mindepth 1 -maxdepth 1 -type d)
    printf "%s\n" "${WALLPAPERS_IDS[@]}"
}


###############################################
#  AUTO RANDOM LOOP
###############################################
cmd_auto_random() {
    log "Starting auto-random mode with delay: $DELAY seconds"
    # Guardar el PID del loop actual
    echo $$ > "$PID_FILE"
    trap 'kill_previous_engine' EXIT

    while true; do
        cmd_random
        sleep "$DELAY"
    done
}


###############################################
#  PARSER DE ARGUMENTOS
###############################################
log "Parsing arguments: $*"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)
            WALLPAPERS_DIRECTORY="$2"
            log "Directory set to: $WALLPAPERS_DIRECTORY"
            shift 2
            ;;
        --set)
            COMMAND="set"
            ARGUMENTS="$2"
            log "Command: set ($ARGUMENTS)"
            shift 2
            ;;
        --random)
            COMMAND="random"
            log "Command: random"
            shift
            ;;
        --list)
            COMMAND="list"
            log "Command: list"
            shift
            ;;
        --delay)
            COMMAND="auto-random"
            DELAY="$2"
            log "Command: auto-random, delay=$DELAY"
            shift 2
            ;;
        --above)
            REMOVE_ABOVE="true"
            log "Flag: remove above priority"
            shift
            ;;
        --pool)
            log "Reading POOL items..."
            shift
            while [[ $# -gt 0 && "$1" != --* ]]; do
                log "POOL += $1"
                POOL+=("$1")
                shift
            done
            ;;
        --sound)
            log "Reading SOUND flags..."
            shift
            # Leer todos los flags de sonido hasta encontrar otro flag principal (--) o fin de argumentos
            while [[ $# -gt 0 ]]; do
                case "$1" in
                    --silent)
                        SOUND_ARGS+=("--silent")
                        log "SOUND_FLAG: --silent (mute background audio)"
                        shift
                        ;;
                    --volume)
                        if [[ $# -lt 2 ]]; then
                            log "ERROR: --volume requires a value"
                            shift
                            break
                        fi
                        SOUND_ARGS+=("--volume" "$2")
                        log "SOUND_FLAG: --volume $2"
                        shift 2
                        ;;
                    --noautomute)
                        SOUND_ARGS+=("--noautomute")
                        log "SOUND_FLAG: --noautomute (don't mute when other apps play audio)"
                        shift
                        ;;
                    --no-audio-processing)
                        SOUND_ARGS+=("--no-audio-processing")
                        log "SOUND_FLAG: --no-audio-processing (disable audio reactive features)"
                        shift
                        ;;
                    --*)
                        # Encontramos otro flag principal, salir del loop de sonido
                        log "End of sound flags, found: $1"
                        break
                        ;;
                    *)
                        log "WARNING: Unknown sound flag: $1 (ignoring)"
                        shift
                        ;;
                esac
            done
            ;;
        --stop)
            COMMAND="stop"
            log "Command: stop"
            shift
            ;;
        *)
            ENGINE_ARGS+=("$1")
            log "ENGINE_ARG += $1"
            shift
            ;;
    esac
done


###############################################
#  EJECUCIÓN
###############################################
log "Executing command: $COMMAND"

case "$COMMAND" in
    random) cmd_random ;;
    set) cmd_set "$ARGUMENTS" ;;
    list) cmd_list ;;
    auto-random) cmd_auto_random ;;
    stop) cmd_stop ;;
    *)
        log "ERROR: No command specified"
        echo "No command specified"
        exit 1
        ;;
esac
