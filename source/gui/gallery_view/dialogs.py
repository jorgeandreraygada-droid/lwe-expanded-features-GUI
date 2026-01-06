from tkinter import Toplevel, Label, Entry, Button, Frame, Listbox, ttk
from gui.groups import create_group, add_to_group, remove_from_group, in_group


class DialogManager:
    """Gestiona los diálogos de la aplicación"""
    
    def __init__(self, parent, config, log_callback=None):
        self.parent = parent
        self.config = config
        self.log_callback = log_callback
    
    def log(self, message):
        """Envía mensaje al log si existe callback"""
        if self.log_callback:
            self.log_callback(message)
    
    def show_new_group_dialog(self, on_created=None):
        """
        Muestra diálogo para crear un nuevo grupo
        
        on_created: callback que se ejecuta después de crear el grupo
        """
        win = Toplevel(self.parent)
        win.title("New group")
        win.geometry("250x120")
        win.config(bg="#0a0e27")
        
        Label(win, text="Group name:", bg="#0a0e27", fg="#00d4ff", font=("Arial", 10, "bold")).pack(pady=5)
        entry = Entry(win, bg="#1a2f4d", fg="#00d4ff", insertbackground="#00d4ff", font=("Arial", 10))
        entry.pack(pady=5)
        entry.focus()
        
        def create():
            name = entry.get().strip()
            if name:
                if create_group(self.config, name):
                    self.log(f"[GUI] Created group: {name}")
                else:
                    self.log(f"[GUI] Group '{name}' already exists")
            win.destroy()
            if on_created:
                on_created()
        
        def on_enter(event):
            create()
        
        entry.bind("<Return>", on_enter)
        Button(win, text="CREATE", bg="#00d4ff", fg="#0a0e27", font=("Arial", 10, "bold"), activebackground="#00ffff", activeforeground="#0a0e27", bd=2, relief="raised", cursor="hand2", command=create).pack(pady=10)
    
    def show_assign_groups_dialog(self, wallpaper_id, on_closed=None):
        """
        Muestra diálogo para asignar/desasignar grupos a un wallpaper
        
        on_closed: callback que se ejecuta al cerrar el diálogo
        """
        win = Toplevel(self.parent)
        win.title(f"Assign groups: {wallpaper_id}")
        win.geometry("500x450")
        
        Label(win, text="Groups").pack(pady=5)
        
        # Lista con scrollbar
        list_frame = Frame(win)
        list_frame.pack(fill="both", expand=True)
        
        groups_list = Listbox(list_frame, selectmode="single")
        groups_list.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=groups_list.yview)
        scrollbar.pack(side="right", fill="y")
        groups_list.config(yscrollcommand=scrollbar.set)
        
        def refresh_list():
            """Refresca la lista de grupos mostrando cuáles están asignados"""
            groups_list.delete(0, "end")
            for g in self.config["--groups"].keys():
                mark = "✓ " if in_group(self.config, g, wallpaper_id) else "  "
                groups_list.insert("end", f"{mark}{g}")
        
        refresh_list()
        
        def get_selected_group():
            """Obtiene el grupo seleccionado en la lista"""
            sel = groups_list.curselection()
            if not sel:
                return None
            text = groups_list.get(sel[0])
            # Remover el marcador (✓ o espacios)
            if text.startswith("✓ ") or text.startswith("  "):
                return text[2:].strip()
            return text.strip()
        
        def add_selected():
            """Añade el wallpaper al grupo seleccionado"""
            g = get_selected_group()
            if g:
                add_to_group(self.config, g, wallpaper_id)
                refresh_list()
                self.log(f"[GUI] Added {wallpaper_id} to group '{g}'")
        
        def remove_selected():
            """Elimina el wallpaper del grupo seleccionado"""
            g = get_selected_group()
            if g:
                remove_from_group(self.config, g, wallpaper_id)
                refresh_list()
                self.log(f"[GUI] Removed {wallpaper_id} from group '{g}'")
        
        # Botones de añadir/eliminar
        btn_frame = Frame(win)
        btn_frame.pack(pady=5)
        
        Button(btn_frame, text="Add", command=add_selected).grid(row=0, column=0, padx=5)
        Button(btn_frame, text="Remove", command=remove_selected).grid(row=0, column=1, padx=5)
        
        # Sección para crear nuevo grupo y añadir directamente
        Label(win, text="New group:").pack(pady=(10, 0))
        new_entry = Entry(win)
        new_entry.pack(pady=5)
        
        def create_and_add():
            """Crea un nuevo grupo y añade el wallpaper directamente"""
            name = new_entry.get().strip()
            if not name:
                return
            
            if create_group(self.config, name):
                add_to_group(self.config, name, wallpaper_id)
                refresh_list()
                new_entry.delete(0, "end")
                self.log(f"[GUI] Created group '{name}' and added {wallpaper_id}")
            else:
                self.log(f"[GUI] Group '{name}' already exists")
        
        def on_enter(event):
            create_and_add()
        
        new_entry.bind("<Return>", on_enter)
        Button(win, text="Create & add", command=create_and_add).pack(pady=5)
        
        # Botón cerrar
        def close():
            if on_closed:
                on_closed()
            win.destroy()
        
        Button(win, text="Close", command=close).pack(pady=10)
        
        # Permitir cerrar con doble-click en un grupo
        def on_double_click(event):
            g = get_selected_group()
            if g:
                if in_group(self.config, g, wallpaper_id):
                    remove_selected()
                else:
                    add_selected()
        
        groups_list.bind("<Double-Button-1>", on_double_click)