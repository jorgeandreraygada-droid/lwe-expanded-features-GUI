from gui.wallpaper_loader import THUMB_SIZE
from gui.gallery_view.thumbnails import ThumbnailFactory
from gui.gallery_view.context_menus import ContextMenuManager
from gui.gallery_view.dialogs import DialogManager
from gui.groups import toggle_favorite, add_to_group, delete_group, in_group, remove_from_group


class GalleryView:
    """Gestiona la visualización de la galería de wallpapers y grupos"""
    
    def __init__(self, canvas, inner_frame, config, loader, log_callback=None):
        self.canvas = canvas
        self.inner_frame = inner_frame
        self.config = config
        self.loader = loader
        self.log_callback = log_callback
        
        # Estado de la galería
        self.item_list = []
        self.thumbnail_widgets = {}
        self.current_view = "groups"
        self.current_group = None
        self.current_wallpaper = None
        
        # Configuración de layout
        self.max_cols = 6
        self.row_height = THUMB_SIZE[1] + 40
        
        # Componentes auxiliares
        self.thumbnails = ThumbnailFactory(inner_frame, config)
        self.context_menu_manager = ContextMenuManager(canvas, config)
        self.dialog_manager = DialogManager(canvas, config, log_callback)
        
        # Callbacks externos (serán configurados por main.py)
        self.on_wallpaper_applied = None
        self.on_refresh_needed = None
    
    def log(self, message):
        """Envía un mensaje al callback de log"""
        if self.log_callback:
            self.log_callback(message)
    
    def clear_gallery(self):
        """Limpia todos los widgets de la galería"""
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.thumbnail_widgets = {}
    
    # ========== Creación de thumbnails ==========
    
    def create_group_thumbnail(self, index, row, col, group_id, name, count):
        """Crea un thumbnail de grupo"""
        frame = self.thumbnails.create_group_thumbnail(
            index, row, col, group_id, name, count,
            on_click=self.open_group,
            on_right_click=self._handle_group_right_click
        )
        self.thumbnail_widgets[index] = frame
    
    def create_new_group_thumbnail(self, index, row, col):
        """Crea el thumbnail para crear un nuevo grupo"""
        frame = self.thumbnails.create_new_group_thumbnail(
            index, row, col,
            on_click=self._handle_new_group_click
        )
        self.thumbnail_widgets[index] = frame
    
    def create_wallpaper_thumbnail(self, index, row, col, wallpaper_id, img):
        """Crea un thumbnail de wallpaper"""
        frame = self.thumbnails.create_wallpaper_thumbnail(
            index, row, col, wallpaper_id, img,
            current_wallpaper=self.current_wallpaper,
            on_double_click=self.apply_wallpaper,
            on_right_click=self._handle_wallpaper_right_click
        )
        self.thumbnail_widgets[index] = frame
    
    # ========== Acciones de wallpapers ==========
    
    def apply_wallpaper(self, wallpaper_id):
        """Aplica un wallpaper (double click)"""
        self.current_wallpaper = wallpaper_id
        self.log(f"[GUI] Applying wallpaper: {wallpaper_id}")
        if self.on_wallpaper_applied:
            self.on_wallpaper_applied(wallpaper_id)
    
    # ========== Navegación ==========
    
    def open_group(self, group_id):
        """Abre un grupo para ver sus wallpapers"""
        self.current_view = "wallpapers"
        self.current_group = group_id
        if self.on_refresh_needed:
            self.on_refresh_needed()
    
    def go_back(self):
        """Vuelve a la vista de grupos"""
        self.current_view = "groups"
        self.current_group = None
        if self.on_refresh_needed:
            self.on_refresh_needed()
    
    # ========== Manejadores de eventos (privados) ==========
    
    def _handle_wallpaper_right_click(self, event, wallpaper_id):
        """Maneja el click derecho en un wallpaper"""
        callbacks = {
            'on_toggle_favorite': self._toggle_favorite_and_refresh,
            'on_assign_groups': self._show_assign_groups_dialog,
            'on_add_to_group': self._add_to_group_and_refresh,
            'on_mark_not_working': self._toggle_not_working_and_refresh
        }
        self.context_menu_manager.show_wallpaper_menu(event, wallpaper_id, callbacks)
    
    def _handle_group_right_click(self, event, group_id):
        """Maneja el click derecho en un grupo"""
        self.context_menu_manager.show_group_menu(
            event, group_id,
            on_delete=self._delete_group_and_refresh
        )
    
    def _handle_new_group_click(self):
        """Maneja el click en el botón de nuevo grupo"""
        self.dialog_manager.show_new_group_dialog(
            on_created=self.on_refresh_needed
        )
    
    # ========== Operaciones con refresh automático ==========
    
    def _toggle_favorite_and_refresh(self, wallpaper_id):
        """Toggle favorito y refresca la galería"""
        toggle_favorite(self.config, wallpaper_id)
        if self.on_refresh_needed:
            self.on_refresh_needed()
    
    def _toggle_not_working_and_refresh(self, wallpaper_id):
        """Toggle estado 'not working' y refresca la galería"""
        if in_group(self.config, "not working", wallpaper_id):
            remove_from_group(self.config, "not working", wallpaper_id)
            self.log(f"[GUI] Removed {wallpaper_id} from 'not working'")
        else:
            add_to_group(self.config, "not working", wallpaper_id)
            self.log(f"[GUI] Added {wallpaper_id} to 'not working'")
        if self.on_refresh_needed:
            self.on_refresh_needed()
    
    def _add_to_group_and_refresh(self, group, wallpaper_id):
        """Añade a grupo y refresca la galería"""
        add_to_group(self.config, group, wallpaper_id)
        self.log(f"[GUI] Added {wallpaper_id} to group '{group}'")
        if self.on_refresh_needed:
            self.on_refresh_needed()
    
    def _delete_group_and_refresh(self, group_id):
        """Elimina un grupo y refresca la galería"""
        delete_group(self.config, group_id)
        self.log(f"[GUI] Deleted group '{group_id}'")
        if self.on_refresh_needed:
            self.on_refresh_needed()
    
    def _show_assign_groups_dialog(self, wallpaper_id):
        """Muestra el diálogo de asignación de grupos"""
        self.dialog_manager.show_assign_groups_dialog(
            wallpaper_id,
            on_closed=self.on_refresh_needed
        )