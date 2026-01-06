import json
from os import path, makedirs

CONFIG_PATH = path.join(path.dirname(__file__), "..", "core", "config.json")

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
    "--favorites": [],
    "--groups": {
        "not working": []
    },
    "--pool": [],
    "--show-logs": True
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


def build_args(config):
    """Construye los argumentos para el script bash en el orden correcto"""
    args = []

    # 1. --dir (siempre primero si existe)
    dir_path = config.get("--dir")
    if dir_path:
        args.extend(["--dir", dir_path])

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