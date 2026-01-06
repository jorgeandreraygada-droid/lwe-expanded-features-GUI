from tkinter import Menu
from gui.groups import is_favorite, in_group


class ContextMenuManager:
    """Gestiona los menús contextuales de la aplicación"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
    
    def show_wallpaper_menu(self, event, wallpaper_id, callbacks):
        """
        Muestra el menú contextual de un wallpaper
        
        callbacks debe contener:
        - on_toggle_favorite: función que recibe wallpaper_id
        - on_assign_groups: función que recibe wallpaper_id
        - on_add_to_group: función que recibe (group, wallpaper_id)
        - on_mark_not_working: función que recibe wallpaper_id
        """
        menu = Menu(self.parent, tearoff=0, bg="#1a2f4d", fg="#00d4ff", activebackground="#00d4ff", activeforeground="#0a0e27")
        
        # Opción de favoritos
        if is_favorite(self.config, wallpaper_id):
            menu.add_command(
                label="Remove from favorites",
                command=lambda: callbacks['on_toggle_favorite'](wallpaper_id)
            )
        else:
            menu.add_command(
                label="Add to favorites",
                command=lambda: callbacks['on_toggle_favorite'](wallpaper_id)
            )
        
        menu.add_separator()
        
        # Opción de marcar como "not working"
        if in_group(self.config, "not working", wallpaper_id):
            menu.add_command(
                label="Remove from not working",
                command=lambda: callbacks['on_mark_not_working'](wallpaper_id)
            )
        else:
            menu.add_command(
                label="Mark as not working",
                command=lambda: callbacks['on_mark_not_working'](wallpaper_id)
            )
        
        menu.add_separator()
        
        # Opción de asignar grupos (diálogo completo)
        menu.add_command(
            label="Assign to group",
            command=lambda: callbacks['on_assign_groups'](wallpaper_id)
        )
        
        # Submenu de añadir rápido a grupo (excluir "not working")
        groups_menu = Menu(menu, tearoff=0, bg="#1a2f4d", fg="#00d4ff", activebackground="#00d4ff", activeforeground="#0a0e27")
        groups = [g for g in self.config["--groups"].keys() if g != "not working"]
        
        if groups:
            for g in groups:
                groups_menu.add_command(
                    label=g,
                    command=lambda group=g: callbacks['on_add_to_group'](group, wallpaper_id)
                )
        else:
            groups_menu.add_command(label="No groups", state="disabled")
        
        menu.add_cascade(label="Add to group", menu=groups_menu)
        
        menu.tk_popup(event.x_root, event.y_root)
    
    def show_group_menu(self, event, group_id, on_delete):
        """
        Muestra el menú contextual de un grupo
        
        on_delete: función que recibe group_id
        """
        menu = Menu(self.parent, tearoff=0, bg="#1a2f4d", fg="#000000", activebackground="#661111", activeforeground="#ffffff")
        
        if group_id not in ("__ALL__", "__FAVORITES__", "not working"):
            menu.add_command(
                label=f"Delete group '{group_id}'",
                command=lambda: on_delete(group_id)
            )
        else:
            menu.add_command(label="Cannot delete this folder", state="disabled")
        
        menu.tk_popup(event.x_root, event.y_root)