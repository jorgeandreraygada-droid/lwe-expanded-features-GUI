from PIL import Image, ImageTk
from os import path, listdir

THUMB_SIZE = (120, 100)


def calculate_dynamic_thumb_size(screen_width, desired_columns=8):
    """
    Calcula el tamaño de thumbnail dinámicamente basándose en el ancho de pantalla.
    
    Args:
        screen_width: Ancho de la resolución de pantalla
        desired_columns: Número deseado de columnas (por defecto 8)
    
    Returns:
        Tupla (width, height) con el tamaño calculado
    """
    padding_per_thumb = 40  # padding alrededor de cada thumbnail
    available_width = screen_width - (padding_per_thumb * desired_columns)
    thumb_width = max(80, available_width // desired_columns)  # mínimo 80px
    # Mantener proporción aspect ratio aproximada (100:112 ≈ 0.89)
    thumb_height = int(thumb_width * 1.12)
    return (thumb_width, thumb_height)


class WallpaperLoader:
    """Gestiona la carga y caché de previews de wallpapers"""
    
    def __init__(self):
        self.preview_cache = {}
    
    def load_preview(self, wallpaper_folder):
        """Carga la imagen de preview de un wallpaper"""
        if wallpaper_folder in self.preview_cache:
            return self.preview_cache[wallpaper_folder]
        
        for name in ("preview.jpg", "preview.png", "preview.gif"):
            full_path = path.join(wallpaper_folder, name)
            if path.exists(full_path):
                img = Image.open(full_path)
                img.thumbnail(THUMB_SIZE)
                tk_img = ImageTk.PhotoImage(img)
                self.preview_cache[wallpaper_folder] = tk_img
                return tk_img
        return None
    
    def clear_cache(self):
        """Limpia el caché de previews"""
        self.preview_cache.clear()


def count_all_wallpapers(root_dir, loader):
    """Cuenta todos los wallpapers con preview"""
    if not root_dir:
        return 0
    count = 0
    for w in listdir(root_dir):
        folder = path.join(root_dir, w)
        if not path.isdir(folder):
            continue
        if loader.load_preview(folder):
            count += 1
    return count


def count_favorite_wallpapers(root_dir, favorites, loader):
    """Cuenta los wallpapers favoritos con preview"""
    if not root_dir:
        return 0
    favs = set(favorites)
    count = 0
    for w in listdir(root_dir):
        folder = path.join(root_dir, w)
        if not path.isdir(folder):
            continue
        if w in favs and loader.load_preview(folder):
            count += 1
    return count


def get_wallpapers_list(root_dir, loader, group=None, favorites=None, groups_dict=None):
    """Obtiene la lista de wallpapers según el grupo seleccionado"""
    if not root_dir:
        return []
    
    # Primero: todos los wallpapers válidos (con preview)
    all_with_preview = []
    for w in listdir(root_dir):
        folder = path.join(root_dir, w)
        if not path.isdir(folder):
            continue
        if loader.load_preview(folder):
            all_with_preview.append(w)
    
    if group is None or group == "__ALL__":
        return all_with_preview
    
    elif group == "__FAVORITES__":
        favs = set(favorites or [])
        return [w for w in all_with_preview if w in favs]
    
    else:
        group_list = (groups_dict or {}).get(group, [])
        return [w for w in all_with_preview if w in group_list]