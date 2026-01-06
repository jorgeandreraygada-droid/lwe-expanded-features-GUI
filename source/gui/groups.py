from gui.config import save_config
from shutil import rmtree
from os import path

# Logs globales (se sobrescribirán desde gui_engine si es necesario)
_log_callback = None

def set_log_callback(callback):
    """Configura el callback de logging"""
    global _log_callback
    _log_callback = callback

def _log(message):
    """Función de log centralizada"""
    if _log_callback:
        _log_callback(f"[GROUPS] {message}")
    else:
        print(f"[GROUPS] {message}")


def toggle_favorite(config, wallpaper_id):
    """Alterna el estado de favorito de un wallpaper"""
    favs = config["--favorites"]

    if wallpaper_id in favs:
        favs.remove(wallpaper_id)
        _log(f"Removed {wallpaper_id} from favorites")
    else:
        favs.append(wallpaper_id)
        _log(f"Added {wallpaper_id} to favorites")

    save_config(config)


def is_favorite(config, wallpaper_id):
    """Verifica si un wallpaper es favorito"""
    return wallpaper_id in config["--favorites"]


def create_group(config, name):
    """Crea un nuevo grupo"""
    name = name.strip()
    if not name:
        _log(f"Cannot create group with empty name")
        return False
    
    groups = config["--groups"]
    if name not in groups:
        groups[name] = []
        save_config(config)
        _log(f"Created group '{name}'")
        return True
    _log(f"Group '{name}' already exists")
    return False


def add_to_group(config, group, wallpaper_id):
    """Añade un wallpaper a un grupo"""
    groups = config["--groups"]
    if group not in groups:
        groups[group] = []
    wallpaper_id = str(wallpaper_id)
    if wallpaper_id not in groups[group]:
        groups[group].append(wallpaper_id)
        save_config(config)
        _log(f"Added {wallpaper_id} to group '{group}'")
    else:
        _log(f"{wallpaper_id} already in group '{group}'")


def remove_from_group(config, group, wallpaper_id):
    """Elimina un wallpaper de un grupo"""
    groups = config["--groups"]
    wallpaper_id = str(wallpaper_id)
    if group in groups and wallpaper_id in groups[group]:
        groups[group].remove(wallpaper_id)
        save_config(config)
        _log(f"Removed {wallpaper_id} from group '{group}'")
    else:
        _log(f"{wallpaper_id} not found in group '{group}'")


def in_group(config, group, wallpaper_id):
    """Verifica si un wallpaper está en un grupo"""
    return str(wallpaper_id) in config["--groups"].get(group, [])


def delete_group(config, group_id):
    """Elimina un grupo"""
    if group_id in config["--groups"]:
        del config["--groups"][group_id]
        save_config(config)
        _log(f"Deleted group '{group_id}'")
    else:
        _log(f"Group '{group_id}' not found")


def delete_not_working_wallpapers(config):
    """Elimina los wallpapers del grupo 'not working' del directorio"""
    wallpaper_dir = config.get("--dir")
    not_working_list = config.get("--groups", {}).get("not working", [])
    
    if not wallpaper_dir:
        _log("No wallpaper directory configured")
        return
    
    if not not_working_list:
        _log("No wallpapers in 'not working' group")
        return
    
    _log(f"Starting deletion of {len(not_working_list)} wallpapers from 'not working' group")
    
    deleted_count = 0
    for wallpaper_id in not_working_list:
        wallpaper_path = path.join(wallpaper_dir, str(wallpaper_id))
        
        if path.exists(wallpaper_path) and path.isdir(wallpaper_path):
            try:
                rmtree(wallpaper_path)
                deleted_count += 1
                _log(f"Deleted wallpaper: {wallpaper_id}")
            except Exception as e:
                _log(f"Error deleting wallpaper {wallpaper_id}: {e}")
        else:
            _log(f"Wallpaper not found: {wallpaper_id}")
    
    # Limpiar el grupo después de eliminar los wallpapers
    config["--groups"]["not working"] = []
    save_config(config)
    _log(f"Deletion complete: {deleted_count}/{len(not_working_list)} wallpapers deleted")