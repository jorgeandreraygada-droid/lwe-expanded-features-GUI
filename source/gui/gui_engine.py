from tkinter import Tk
from os import path

# Módulos propios - Configuración y Core
from gui.config import load_config, merge_config, DEFAULT_CONFIG, save_config
from gui.wallpaper_loader import WallpaperLoader, THUMB_SIZE
from gui.engine_controller import EngineController
from gui.gallery_view.gallery_view import GalleryView
from gui.groups import delete_not_working_wallpapers, set_log_callback

# Componentes UI
from gui.ui_components.log_area import LogArea 
from gui.ui_components.directory_controls import DirectoryControls
from gui.ui_components.flags import FlagsPanel
from gui.ui_components.sound_panel import SoundPanel  # ← NUEVO
from gui.ui_components.gallery_canvas import GalleryCanvas
from gui.event_handler.event_handler import EventHandlers
from gui.gallery_view.gallery_manager import GalleryManager


class WallpaperEngineGUI:
    """Clase principal de la aplicación GUI"""
    
    def __init__(self):
        # Ventana principal
        self.main_window = Tk()
        self.main_window.title("Linux Wallpaper Engine GUI")
        self.main_window.config(bg="#1F0120")
        # Ajustar tamaño inicial a la resolución de pantalla
        self.main_window.update_idletasks()
        # sw = self.main_window.winfo_screenwidth()
        # sh = self.main_window.winfo_screenheight()
        # Reservar un pequeño margen para la barra del sistema
        # geom_w = sw
        # geom_h = sh
        self.main_window.geometry(f"{800}x{600}+0+0")
        self.main_window.minsize(800, 600)
        self.main_window.resizable(True, True)
        # Hacer que la fila de la galería (1) se expanda con la ventana
        self.main_window.rowconfigure(1, weight=1)
        # Log area en fila 3 mantiene tamaño fijo (weight 0)
        self.main_window.rowconfigure(3, weight=0)
        # Columna 0 (canvas) se expande, columna 1 (flags) mantiene tamaño mínimo
        self.main_window.columnconfigure(0, weight=1)
        self.main_window.columnconfigure(1, weight=0)
        
        # Cargar configuración
        self._load_config()
        
        # Create log area FIRST - needed for logging callbacks
        self.log_area = LogArea(self.main_window)
        self.log_area.grid(column=0, row=3, columnspan=2, sticky="nsew")
        
        # Inicializar componentes core (now logging will work)
        self.loader = WallpaperLoader()
        self.engine = EngineController(DEFAULT_CONFIG, self._log)
        
        # Configurar logging para grupos
        set_log_callback(self._log)
        
        # Crear UI (skip log_area since already created)
        self._create_ui()
        
        # Crear GalleryView
        self._create_gallery_view()
        
        # Crear managers
        self._create_managers()
        
        # Conectar callbacks
        self._connect_callbacks()
        
        # Inicializar valores
        self._initialize_ui_values()
        
        # Cargar logs del backend
        self._load_backend_logs()
        
        # Refrescar galería inicial
        self.gallery_manager.refresh()
        
        # Configurar evento de cierre de ventana
        self.main_window.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    # ========== Inicialización ==========
    
    def _load_config(self):
        """Carga y merge la configuración"""
        config = load_config()
        merge_config(DEFAULT_CONFIG, config)
        if DEFAULT_CONFIG["--dir"]:
            expanded_dir = path.expanduser(DEFAULT_CONFIG["--dir"])
            # Si el directorio no existe, limpiar el config
            if path.exists(expanded_dir) and path.isdir(expanded_dir):
                DEFAULT_CONFIG["--dir"] = expanded_dir
            else:
                DEFAULT_CONFIG["--dir"] = ""

    
    def _create_ui(self):
        """Crea todos los componentes de la UI (excepto log_area que se crea antes)"""
        # Log area is already created during __init__ to ensure logging works
        # before other components are initialized
        
        # Directory controls
        self.directory_controls = DirectoryControls(self.main_window)
        self.directory_controls.grid(column=0, row=0, sticky="nsew")
        
        # Flags panel
        self.flags_panel = FlagsPanel(self.main_window)
        self.flags_panel.grid(column=1, row=0, sticky="nsew")
        
        # Sound panel ← NUEVO
        self.sound_panel = SoundPanel(self.main_window)
        self.sound_panel.grid(column=1, row=1, sticky="nsew", padx=(5, 0), pady=(5, 0))
        
        # Gallery canvas
        self.gallery_canvas = GalleryCanvas(self.main_window)
        self.gallery_canvas.grid(column=0, row=1, columnspan=1, sticky="nsew")
    
    def _create_gallery_view(self):
        """Crea la vista de galería"""
        self.gallery_view = GalleryView(
            self.gallery_canvas.canvas,
            self.gallery_canvas.inner_frame,
            DEFAULT_CONFIG,
            self.loader,
            self._log
        )
    
    def _create_managers(self):
        """Crea los managers de la aplicación"""
        # UI components dict para EventHandlers
        ui_components = {
            'main_window': self.main_window,
            'directory_controls': self.directory_controls,
            'flags_panel': self.flags_panel,
            'sound_panel': self.sound_panel,
            'gallery_canvas': self.gallery_canvas,
            'on_refresh_gallery': lambda: self._refresh_with_scroll_update(),
            'on_execute': self._on_execute
        }
        
        # Event handlers
        self.event_handlers = EventHandlers(
            DEFAULT_CONFIG,
            ui_components,
            self._log
        )
        
        # Gallery manager
        self.gallery_manager = GalleryManager(
            self.gallery_view,
            self.loader,
            DEFAULT_CONFIG
        )
        # initial max cols placeholder (will be computed once canvas has size)
        self.gallery_view.max_cols = getattr(self.gallery_view, "max_cols", 6)
        # NOTE: resize handler moved to instance method `_on_canvas_resize`
    
    def _connect_callbacks(self):
        """Conecta todos los callbacks de eventos"""
        # Directory controls
        self.directory_controls.pick_button.config(
            command=self.event_handlers.on_pick_directory
        )
        self.directory_controls.explore_button.config(
            command=self.event_handlers.on_explore_directory
        )
        self.directory_controls.execute_button.config(
            command=self.event_handlers.on_execute
        )
        self.directory_controls.stop_button.config(
            command=self.event_handlers.on_stop
        )
        
        # Flags panel
        self.flags_panel.window_checkbox.config(
            command=self.event_handlers.on_window_mode_changed
        )
        self.flags_panel.above_checkbox.config(
            command=self.event_handlers.on_above_flag_changed
        )
        self.flags_panel.random_checkbox.config(
            command=self.event_handlers.on_random_mode_changed
        )
        self.flags_panel.logs_checkbox.config(
            command=self._on_logs_visibility_changed
        )
        self.flags_panel.back_button.config(
            command=self._on_back
        )
        self.flags_panel.clear_log_button.config(
            command=self.log_area.clear
        )
        
        # Sound panel ← NUEVO
        self.sound_panel.silent_checkbox.config(
            command=self.event_handlers.on_silent_changed
        )
        """VOlUME PANEL NOT WORKING
        REFER TO CLOSED ISSUE ON VOLUME PANEL"""
        # self.sound_panel.volume_slider.config(
            #command=self.event_handlers.on_volume_changed
        #)
        self.sound_panel.noautomute_checkbox.config(
            command=self.event_handlers.on_noautomute_changed
        )
        self.sound_panel.no_audio_processing_checkbox.config(
            command=self.event_handlers.on_audio_processing_changed
        )
        
        # Gallery canvas
        self.gallery_canvas.inner_frame.bind(
            "<Configure>",
            self.gallery_canvas.update_scroll_region
        )
        self.gallery_canvas.bind_scroll_events(
            self.event_handlers.on_mousewheel
        )
        # Recalcular columnas mientras la app está en ejecución
        try:
            self.gallery_canvas.canvas.bind("<Configure>", self._on_canvas_resize)
        except Exception:
            pass
        try:
            self.gallery_canvas.container.bind("<Configure>", self._on_canvas_resize)
        except Exception:
            pass
        try:
            self.main_window.bind("<Configure>", self._on_canvas_resize)
        except Exception:
            pass
        
        # Gallery view callbacks
        self.gallery_view.on_wallpaper_applied = self._on_wallpaper_applied
        self.gallery_view.on_refresh_needed = self._refresh_with_scroll_update
    
    def _initialize_ui_values(self):
        """Inicializa los valores de la UI desde la configuración"""
        self.directory_controls.set_directory(str(DEFAULT_CONFIG["--dir"]))
        self.flags_panel.window_mode.set(DEFAULT_CONFIG["--window"]["active"])
        # "remove above prio" marcado = --above debe ser True (para remover always-on-top)
        self.flags_panel.above_flag.set(DEFAULT_CONFIG["--above"])
        self.flags_panel.random_mode.set(
            DEFAULT_CONFIG["--random"] or DEFAULT_CONFIG["--delay"]["active"]
        )
        # Cargar estado de logs desde configuración
        logs_visible = DEFAULT_CONFIG.get("--show-logs", True)
        self.flags_panel.logs_visible.set(logs_visible)
        # Aplicar la visibilidad del LogArea según la configuración cargada
        if logs_visible:
            self.log_area.grid_show()
        else:
            self.log_area.grid_remove()
        
        # Inicializar valores de sonido
        sound_config = DEFAULT_CONFIG.get("--sound", {})
        self.sound_panel.silent.set(sound_config.get("silent", False))
        self.sound_panel.noautomute.set(sound_config.get("noautomute", False))
        self.sound_panel.no_audio_processing.set(sound_config.get("no_audio_processing", False))
        
        """VOLUMEN PANEL"""
        """Actualmente el Panel de volumen está ocasionando behaviour muy raro, como por ejemplo ignorar el flag de --above, 
        crear subprocesos huérfanos, y realmente tampoco está modificando el volumen real. Se mantendrá como un issue cerrado, 
        ya que no planeo implementar un control de volumen manualmente... (existe el mezclador de audio del entorno gráfico)."""
        # Volumen (None significa que no se especifica)
        # volume = sound_config.get("volume")
        # if volume is not None:
        #    self.sound_panel.set_volume(volume)
        
        # Calcular columnas iniciales para la galería según el tamaño estático de thumbnail
        try:
            self.main_window.update_idletasks()
            # Usar el ancho máximo de pantalla y tamaño estático de thumbnail
            screen_width = self.main_window.winfo_screenwidth()
            col_width = THUMB_SIZE[0]  # tamaño thumb
            initial_cols = max(1, screen_width // col_width) if col_width > 0 else 6
            self.gallery_view.max_cols = initial_cols
        except Exception:
            pass

    def _on_canvas_resize(self, event=None):
        """Handler que recalcula max_cols según el tamaño estático de thumbnail."""
        try:
            # Usar la resolución de pantalla y tamaño estático de thumbnail
            screen_width = self.main_window.winfo_screenwidth()
            col_width = THUMB_SIZE[0]  # tamaño thumb
            new_cols = max(1, screen_width // col_width) if col_width > 0 else 6
            if new_cols != getattr(self.gallery_view, "max_cols", None):
                self.gallery_view.max_cols = new_cols
                self.gallery_manager.refresh()
        except Exception:
            pass
    
    def _load_backend_logs(self):
        """Carga los logs del backend si existen"""
        log_file = path.expanduser(
            "~/.local/share/linux-wallpaper-engine-features/logs.txt"
        )
        if path.exists(log_file):
            with open(log_file, "r") as f:
                for line in f:
                    self._log("[FILE] " + line.strip())
    
    # ========== Callbacks de galería ==========
    
    def _on_wallpaper_applied(self, wallpaper_id):
        """Callback cuando se aplica un wallpaper"""
        # Respetar el estado actual del checkbox "remove above prio"
        # Si está marcado (True), entonces --above debe ser True
        # Si NO está marcado (False), entonces --above debe ser False
        above_value = self.flags_panel.above_flag.get()
        
        # Actualizar la configuración con el estado actual del checkbox
        DEFAULT_CONFIG["--above"] = above_value
        
        # Aplicar el wallpaper (la config ya tiene el valor correcto de --above)
        self.engine.apply_wallpaper(
            wallpaper_id,
            self.gallery_view.item_list,
            self.gallery_view.current_view
        )
        self._refresh_with_scroll_update()
    
    def _on_back(self):
        """Vuelve a la vista de grupos"""
        self.gallery_view.go_back()
    
    def _on_logs_visibility_changed(self):
        """Maneja el cambio de visibilidad de logs"""
        if self.flags_panel.logs_visible.get():
            self.log_area.grid_show()
            self._log("[GUI] Logs visible")
            DEFAULT_CONFIG["--show-logs"] = True
        else:
            self.log_area.grid_remove()
            self._log("[GUI] Logs hidden")
            DEFAULT_CONFIG["--show-logs"] = False
        save_config(DEFAULT_CONFIG)
    
    def _on_execute(self):
        """Ejecuta el engine con la configuración actual"""
        self._log("[GUI] Deleting 'not working' wallpapers before execution...")
        delete_not_working_wallpapers(DEFAULT_CONFIG)
        self.engine.run_engine(
            self.gallery_view.item_list,
            self.gallery_view.current_view
        )
    
    # ========== Helpers ==========
    
    def _log(self, message):
        """Función de log centralizada"""
        self.log_area.log(message)
    
    def _refresh_with_scroll_update(self):
        """Refresca la galería y actualiza la región de scroll"""
        self.gallery_manager.refresh()
        self.gallery_canvas.canvas.update_idletasks()
        self.gallery_canvas.update_scroll_region()
    
    def _on_window_close(self):
        """Maneja el cierre de la ventana"""
        self._log("[GUI] Closing application, deleting 'not working' wallpapers...")
        delete_not_working_wallpapers(DEFAULT_CONFIG)
        self._log("[GUI] Cleanup complete, exiting.")
        self.main_window.destroy()
    
    # ========== Main loop ==========
    
    def run(self):
        """Inicia el mainloop de la aplicación"""
        self.main_window.mainloop()


if __name__ == "__main__":
    app = WallpaperEngineGUI()
    app.run()