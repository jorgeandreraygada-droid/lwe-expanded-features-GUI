from tkinter import filedialog, messagebox, Toplevel, Label, Frame, Button, ttk
from subprocess import Popen
from os import path
from gui.config import update_set_flag, save_config


class EventHandlers:
    """Centraliza todos los manejadores de eventos de la aplicación"""
    
    def __init__(self, config, ui_components, log_callback):
        self.config = config
        self.ui = ui_components
        self.log = log_callback
    
    # ========== Directorio ==========
    
    def on_pick_directory(self):
        """Maneja la selección de directorio"""
        route = filedialog.askdirectory()
        if route:
            self.log(f"[HANDLER] Directory selected: {route}")
            self.ui['directory_controls'].set_directory(route)
            self.config["--dir"] = route
            save_config(self.config)
            if self.ui.get('on_refresh_gallery'):
                self.ui['on_refresh_gallery']()
    
    def on_explore_directory(self):
        """Abre el directorio en el explorador de archivos"""
        try:
            self.log(f"[HANDLER] Opening directory explorer for: {self.config['--dir']}")
            Popen(["xdg-open", self.config["--dir"]])
        except (TypeError, KeyError):
            self.log("[HANDLER] No directory selected, cannot open explorer")
            messagebox.showwarning(
                title="No path selected",
                message="Please, select the Wallpaper Engine Steam Workshop directory before proceeding."
            )
    
    # ========== Flags ==========
    
    def on_window_mode_changed(self):
        """Maneja el cambio de window mode"""
        flags = self.ui['flags_panel']
        if flags.window_mode.get():
            self.log("[HANDLER] Window mode enabled")
            self.config["--window"]["active"] = True
            self.show_resolution_picker()
        else:
            self.log("[HANDLER] Window mode disabled")
            self.config["--window"]["active"] = False
    
    def on_above_flag_changed(self):
        """Maneja el cambio del flag above"""
        flags = self.ui['flags_panel']
        self.config["--above"] = flags.above_flag.get()
        self.log(f"[HANDLER] Above flag changed to: {self.config['--above']}")
    
    def on_random_mode_changed(self):
        """Maneja el cambio de random mode"""
        flags = self.ui['flags_panel']
        
        if flags.random_mode.get():
            self.log("[HANDLER] Random mode enabled")
            # Validar directorio
            if not self.config["--dir"] or not self.config["--dir"].rstrip("/").endswith("431960"):
                self.log("[HANDLER] Invalid directory for random mode")
                messagebox.showwarning(
                    title="Wrong Directory",
                    message="In order for the random mode to work properly, make sure to select the 431960 folder as your root dir!!"
                )
            
            # Mostrar controles de timer
            flags.add_timer_controls(self.on_timer_submit)
        else:
            self.log("[HANDLER] Random mode disabled")
            self.config["--random"] = False
            self.config["--delay"]["active"] = False
            self.config["--delay"]["timer"] = "0"
            flags.clear_dynamic_widgets()
            save_config(self.config)
        
        update_set_flag(self.config)
    
    def on_timer_submit(self, timer_value):
        """Maneja el submit del timer"""
        if timer_value != "0":
            self.log(f"[HANDLER] Delay mode set to {timer_value} seconds")
            self.config["--delay"]["active"] = True
            self.config["--delay"]["timer"] = timer_value
            self.config["--random"] = False
        else:
            self.log("[HANDLER] Random mode (no delay)")
            self.config["--delay"]["active"] = False
            self.config["--delay"]["timer"] = "0"
            self.config["--random"] = True
        
        update_set_flag(self.config)
        save_config(self.config)
        self.ui['flags_panel'].clear_dynamic_widgets()
    
    # ========== Sonido ==========
    
    def on_silent_changed(self):
        """Maneja el cambio del checkbox Silent"""
        sound_panel = self.ui['sound_panel']
        self.config["--sound"]["silent"] = sound_panel.silent.get()
        self.log(f"[HANDLER] Silent mode: {self.config['--sound']['silent']}")
        save_config(self.config)
        
        # Re-aplicar el wallpaper actual si hay uno activo
        current_wallpaper = self.config.get("--set", {}).get("wallpaper")
        if current_wallpaper:
            self.log(f"[HANDLER] Re-applying current wallpaper with new sound settings")
            if self.ui.get('on_execute'):
                self.ui['on_execute']()
    
    """VOLUME PANEL NOT WORKING. REFER TO CLOSED ISSUE."""
    # def on_volume_changed(self, value):
    #    """Maneja el cambio del slider de volumen"""
    #    sound_panel = self.ui['sound_panel']
    #    volume = sound_panel.get_volume()
    #    self.config["--sound"]["volume"] = volume
    #    self.log(f"[HANDLER] Volume set to: {volume}")
    #    save_config(self.config)
        
        # Re-aplicar el wallpaper actual si hay uno activo
    #    current_wallpaper = self.config.get("--set", {}).get("wallpaper")
    #    if current_wallpaper:
    #        self.log(f"[HANDLER] Re-applying current wallpaper with new volume")
    #        if self.ui.get('on_execute'):
    #            self.ui['on_execute']()
    
    def on_noautomute_changed(self):
        """Maneja el cambio del checkbox No Auto Mute"""
        sound_panel = self.ui['sound_panel']
        self.config["--sound"]["noautomute"] = sound_panel.noautomute.get()
        self.log(f"[HANDLER] No auto mute: {self.config['--sound']['noautomute']}")
        save_config(self.config)
        
        # Re-aplicar el wallpaper actual si hay uno activo
        current_wallpaper = self.config.get("--set", {}).get("wallpaper")
        if current_wallpaper:
            self.log(f"[HANDLER] Re-applying current wallpaper with new sound settings")
            if self.ui.get('on_execute'):
                self.ui['on_execute']()
    
    def on_audio_processing_changed(self):
        """Maneja el cambio del checkbox No Audio Processing"""
        sound_panel = self.ui['sound_panel']
        self.config["--sound"]["no_audio_processing"] = sound_panel.no_audio_processing.get()
        self.log(f"[HANDLER] No audio processing: {self.config['--sound']['no_audio_processing']}")
        save_config(self.config)
        
        # Re-aplicar el wallpaper actual si hay uno activo
        current_wallpaper = self.config.get("--set", {}).get("wallpaper")
        if current_wallpaper:
            self.log(f"[HANDLER] Re-applying current wallpaper with new sound settings")
            if self.ui.get('on_execute'):
                self.ui['on_execute']()

    
    # ========== Resolución ==========
    
    def show_resolution_picker(self):
        """Muestra el diálogo de selección de resolución"""
        if hasattr(self, '_resolution_window') and self._resolution_window.winfo_exists():
            return
        
        from gui.config import RESOLUTIONS
        
        window = Toplevel(self.ui['main_window'], padx=5)
        window.title("Pick a resolution")
        window.geometry("185x80")
        self._resolution_window = window
        
        Label(window, text="Pick a resolution").grid(column=0, row=0)
        frame = Frame(window)
        frame.grid(column=0, row=1)
        
        combo = ttk.Combobox(frame, values=RESOLUTIONS, state="readonly")
        combo.grid(column=0, row=0)
        
        def accept():
            selected_res = combo.get()
            window.destroy()
            self.config["--window"]["res"] = selected_res
        
        Button(frame, text="ACCEPT", command=accept).grid(column=0, row=1)
        
        # Seleccionar la resolución actual
        current = 0
        for n, res in enumerate(RESOLUTIONS):
            if res == self.config["--window"]["res"]:
                current = n
                break
        
        combo.current(current)
    
    # ========== Scroll ==========
    
    def on_mousewheel(self, event):
        """Maneja el scroll con la rueda del mouse solo si es necesario"""
        canvas = self.ui['gallery_canvas'].canvas
        
        # Verificar si el contenido es más grande que el viewport
        try:
            canvas_height = canvas.winfo_height()
            content_bbox = canvas.bbox("all")
            if not content_bbox:
                return  # No hay contenido, no hacer scroll
            
            content_height = content_bbox[3] - content_bbox[1]
            
            # Solo permitir scroll si el contenido es más grande que el canvas
            if content_height <= canvas_height:
                return  # No hay scroll necesario
            
            # Hacer scroll
            if event.num == 4:  # Linux scroll up
                canvas.yview_scroll(-3, "units")
            elif event.num == 5:  # Linux scroll down
                canvas.yview_scroll(3, "units")
            else:  # Windows/Mac
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass
    
    # ========== Engine ==========
    
    def on_execute(self):
        """Ejecuta el engine"""
        if self.ui.get('on_execute'):
            self.ui['on_execute']()
    
    def on_stop(self):
        """Detiene el engine"""
        self.log("[GUI] Stopping engine and loops")
        script_path = path.join(path.dirname(__file__), "..", "..", "core", "main.sh")
        proc = Popen([script_path, "--stop"])
        # Use a thread to wait and log completion without blocking GUI
        import threading
        def wait_and_log():
            proc.wait()
            self.log("[GUI] Engine stop command completed")
        threading.Thread(target=wait_and_log, daemon=True).start()