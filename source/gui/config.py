import json
import os
from os import path, makedirs, getenv
from tkinter import messagebox


def get_config_path():
    """Obtiene la ruta de configuración según XDG Base Directory"""
    xdg_config = getenv('XDG_CONFIG_HOME', path.expanduser('~/.config'))
    return path.join(xdg_config, 'linux-wallpaper-engine', 'config.json')


CONFIG_PATH = get_config_path()

RESOLUTIONS = [
    "0x0x0x0",
    "0x0x800x600",
    "0x0x1024x768",
    "0x0x1280x720",
    "0x0x1366x768",
    "0x0x1920x1080",
    "0x0x2560x1440",
    "0x0x3840x2160"
]

DEFAULT_CONFIG = {
    "--window": {
        "active": False,
        "res": "0x0x0x0"
    },
    "--dir": None,
    "--above": False,
    "--delay": {
        "active": False,
        "timer": "0"
    },
    "--random": False,
    "--set": {
        "active": False,
        "wallpaper": ""
    },
    "--sound": {
        "silent": False,
        "volume": None,  # None o valor entre 0-100
        "noautomute": False,
        "no_audio_processing": False
    },
    "--favorites": [],
    "--groups": {},
    "--pool": []
}


def load_config():
    """Carga la configuración desde el archivo JSON"""
    if not path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Guarda la configuración en el archivo JSON"""
    makedirs(path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


def merge_config(defaults, loaded):
    """Merge recursivo de configuraciones"""
    for key, value in loaded.items():
        if key in defaults:
            if isinstance(defaults[key], dict) and isinstance(value, dict):
                merge_config(defaults[key], value)
            else:
                defaults[key] = value
        else:
            defaults[key] = value


def validate_directory(dir_path, log_callback=None):
    """
    Valida que el directorio exista y sea accesible
    
    Args:
        dir_path: Ruta del directorio a validar
        log_callback: Función opcional para logging
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not dir_path:
        return False, "No directory path specified"
    
    if not path.exists(dir_path):
        error_msg = f"Directory does not exist: {dir_path}"
        if log_callback:
            log_callback(f"[WARNING] {error_msg}")
        return False, error_msg
    
    if not path.isdir(dir_path):
        error_msg = f"Path is not a directory: {dir_path}"
        if log_callback:
            log_callback(f"[WARNING] {error_msg}")
        return False, error_msg
    
    # Verificar permisos de lectura
    if not os.access(dir_path, os.R_OK):
        error_msg = f"Directory is not readable: {dir_path}"
        if log_callback:
            log_callback(f"[WARNING] {error_msg}")
        return False, error_msg
    
    return True, None


def build_args(config, log_callback=None, show_gui_warning=False):
    """
    Construye los argumentos para el script bash en el orden correcto
    
    Args:
        config: Diccionario de configuración
        log_callback: Función opcional para logging (ej: gui_log)
        show_gui_warning: Si True, muestra un messagebox de advertencia
    
    Returns:
        list: Lista de argumentos para el script
    """
    args = []

    # 1. --dir (siempre primero si existe Y es válido)
    dir_path = config.get("--dir")
    
    if dir_path:
        is_valid, error_msg = validate_directory(dir_path, log_callback)
        
        if is_valid:
            args.extend(["--dir", dir_path])
            if log_callback:
                log_callback(f"[CONFIG] Directory validated: {dir_path}")
        else:
            # Directorio no válido - notificar pero continuar
            if log_callback:
                log_callback(f"[WARNING] {error_msg}")
                log_callback("[WARNING] Application will continue. Please select a valid directory.")
            
            if show_gui_warning:
                messagebox.showwarning(
                    "Invalid Directory",
                    f"The configured directory could not be found:\n\n{dir_path}\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Please use 'PICK DIR' to select a valid wallpaper directory.\n\n"
                    f"Suggested path:\n"
                    f"~/.steam/steam/steamapps/workshop/content/431960"
                )
            
            # NO añadir el directorio inválido a los args
            # Permitir que la app continúe sin directorio
            return args  # Retornar early sin más argumentos

    else:
        # No hay directorio configurado
        if log_callback:
            log_callback("[INFO] No directory configured yet")
        
        if show_gui_warning:
            messagebox.showinfo(
                "No Directory Selected",
                "No wallpaper directory has been selected.\n\n"
                "Please use 'PICK DIR' to select your wallpaper directory.\n\n"
                "Suggested path:\n"
                "~/.steam/steam/steamapps/workshop/content/431960"
            )
        
        return args  # Retornar early sin argumentos

    # 2. --window (si está activo)
    window_config = config.get("--window", {})
    if isinstance(window_config, dict) and window_config.get("active"):
        res = window_config.get("res", "0x0x0x0")
        args.extend(["--window", res])

    # 3. --above (CRÍTICO: debe estar antes del comando principal)
    if config.get("--above", False):
        args.append("--above")

    # 4. --pool (si existe y tiene contenido)
    pool = config.get("--pool", [])
    if pool and isinstance(pool, list) and len(pool) > 0:
        args.append("--pool")
        args.extend(pool)
    
    # 4.5. --sound (si hay configuración de sonido activa)
    sound_config = config.get("--sound", {})
    if isinstance(sound_config, dict):
        sound_flags = []
        
        # --silent
        if sound_config.get("silent", False):
            sound_flags.append("--silent")
        
        # --volume
        volume = sound_config.get("volume")
        if volume is not None:
            # Validar que el volumen esté en el rango correcto
            try:
                volume_int = int(volume)
                if 0 <= volume_int <= 100:
                    sound_flags.extend(["--volume", str(volume_int)])
                elif log_callback:
                    log_callback(f"[WARNING] Invalid volume value: {volume} (must be 0-100)")
            except (ValueError, TypeError):
                if log_callback:
                    log_callback(f"[WARNING] Invalid volume format: {volume}")
        
        # --noautomute
        if sound_config.get("noautomute", False):
            sound_flags.append("--noautomute")
        
        # --no-audio-processing
        if sound_config.get("no_audio_processing", False):
            sound_flags.append("--no-audio-processing")
        
        # Si hay flags de sonido, añadirlos con el prefijo --sound
        if sound_flags:
            args.append("--sound")
            args.extend(sound_flags)
            if log_callback:
                log_callback(f"[CONFIG] Sound flags: {' '.join(sound_flags)}")

    # 5. Comando principal (mutuamente excluyente: delay, random, o set)
    delay_config = config.get("--delay", {})
    if isinstance(delay_config, dict) and delay_config.get("active"):
        timer = delay_config.get("timer", "0")
        args.extend(["--delay", timer])
    elif config.get("--random", False):
        args.append("--random")
    else:
        set_config = config.get("--set", {})
        if isinstance(set_config, dict):
            wallpaper = set_config.get("wallpaper", "")
            if wallpaper:
                args.extend(["--set", wallpaper])

    return args


def update_set_flag(config):
    """Actualiza el flag --set según el estado de random y delay"""
    if config["--random"] or config["--delay"]["active"]:
        config["--set"]["active"] = False
        config["--set"]["wallpaper"] = ""
    else:
        config["--set"]["active"] = True
        dir_ = config["--dir"]
        if dir_:
            config["--set"]["wallpaper"] = path.basename(dir_)