#!/bin/bash
set -euo pipefail

LOG_FILE="$HOME/.local/share/linux-wallpaper-engine-features/logs.txt"
PID_FILE="$HOME/.local/share/linux-wallpaper-engine-features/loop.pid"
mkdir -p "$(dirname "$LOG_FILE")"

POOL=()
ENGINE=linux-wallpaperengine
ENGINE_ARGS=()
REMOVE_ABOVE="false"
COMMAND=""
DELAY=""
ACTIVE_WIN=""

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg" >> "$LOG_FILE"
}

log "==================== NEW EXECUTION ===================="


###############################################
#  KILL ENGINE (robusto, no mata el nuevo)
###############################################
kill_previous_engine() {
    log "Killing previous engine instances"
    pkill -f linux-wallpaperengine 2>/dev/null || true
}


###############################################
#  STOP TOTAL (mata loops + engine)
###############################################
cmd_stop() {
    log "Stopping ALL wallpaper engine processes and loops"

    # Mata engine
    pkill -9 -f linux-wallpaperengine 2>/dev/null || true

    # Si existe el archivo de PID del loop, mata ese proceso específico
    if [[ -f "$PID_FILE" ]]; then
        local loop_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$loop_pid" ]] && kill -0 "$loop_pid" 2>/dev/null; then
            log "Killing loop process with PID: $loop_pid"
            kill -9 "$loop_pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    
    # Mata cualquier otra instancia de bash ejecutando main.sh (como fallback)
    pkill -9 -f "bash.*main.sh" 2>/dev/null || true
    
    log "Stop command completed"
}


###############################################
#  Esperar ventana del engine (excluyendo antiguas)
###############################################
wait_for_window() {
    local -a exclude_windows=("$@")
    local win=""
    
    for i in {1..200}; do
        local -a current_windows=()
        mapfile -t current_windows < <(wmctrl -lx | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}')
        
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

    log "ERROR: No se pudo encontrar la ventana nueva del engine"
    echo ""
}


###############################################
#  Aplicar flags de ventana
###############################################
apply_window_flags() {
    local win_id="$1"

    if [[ "$REMOVE_ABOVE" == "false" ]]; then
        log "Skipping window flag modifications"
        return
    fi

    log "Applying window flags to $win_id"
    
    wmctrl -i -r "$win_id" -b remove,above
    wmctrl -i -r "$win_id" -b add,skip_pager
    wmctrl -i -r "$win_id" -b add,below

    if [[ -n "$ACTIVE_WIN" ]]; then
        log "Restoring focus to previous window: $ACTIVE_WIN"
        xdotool windowactivate "$ACTIVE_WIN" 2>/dev/null || true
    fi
}


###############################################
#  Aplicar wallpaper (CON TRANSICIÓN SUAVE)
###############################################
apply_wallpaper() {
    local path="$1"

    log "Applying wallpaper: $path"

    # Guardamos las ventanas actuales del engine ANTES de lanzar el nuevo
    local old_windows=()
    mapfile -t old_windows < <(wmctrl -lx | grep -i "linux-wallpaperengine\|wallpaperengine\|steam_app_431960" | awk '{print $1}')
    log "Old engine windows: ${old_windows[*]:-none}"

    ACTIVE_WIN=$(xdotool getactivewindow 2>/dev/null || echo "")
    log "Active window before launch: ${ACTIVE_WIN:-none}"

    # Lanzamos el NUEVO engine
    "$ENGINE" "${ENGINE_ARGS[@]}" "$path" &
    local new_pid=$!
    log "Engine launched with PID $new_pid, args: $ENGINE ${ENGINE_ARGS[*]} $path"

    # Esperamos a que la NUEVA ventana esté lista (excluyendo las antiguas)
    local win_id
    win_id=$(wait_for_window "${old_windows[@]}")

    if [[ -z "$win_id" ]]; then
        log "ERROR: No window found for new engine"
        return
    fi


    apply_window_flags "$win_id"


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