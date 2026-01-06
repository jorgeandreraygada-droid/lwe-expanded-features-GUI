from subprocess import Popen, PIPE
from threading import Thread
from os import path
from gui.config import save_config, build_args


class EngineController:
    """Controlador del wallpaper engine"""
    
    def __init__(self, config, log_callback=None):
        self.config = config
        self.log_callback = log_callback
        # Ruta relativa al directorio actual (source/)
        self.script_path = path.join(path.dirname(__file__), "..", "core", "main.sh")
    
    def log(self, message):
        """Envía un mensaje al callback de log si existe"""
        if self.log_callback:
            self.log_callback(message)
    
    def stop_engine(self):
        """Detiene el engine actual"""
        self.log("[GUI] Stopping previous engine...")
        try:
            stop_proc = Popen(
                [self.script_path, "--stop"],
                stdout=PIPE,
                stderr=PIPE,
                text=True
            )
            stop_proc.wait(timeout=5)
            self.log("[GUI] Previous engine stopped")
        except Exception as e:
            self.log(f"[GUI] Error stopping engine: {e}")
    
    def update_pool(self, item_list, current_view):
        """Actualiza el pool de wallpapers"""
        if not (self.config["--random"] or self.config["--delay"]["active"]):
            self.config["--pool"] = []
            return
        
        if current_view != "wallpapers":
            self.config["--pool"] = []
            return
        
        self.config["--pool"] = item_list.copy()
    
    def run_engine(self, item_list=None, current_view=None):
        """Ejecuta el wallpaper engine con la configuración actual"""
        save_config(self.config)
        
        # Configurar el wallpaper específico si es necesario
        if not self.config["--delay"]["active"] and not self.config["--random"]:
            if not self.config["--set"]["wallpaper"]:
                self.config["--set"]["active"] = True
                dir_ = self.config["--dir"]
                if dir_:
                    wallpaper_id = path.basename(dir_)
                    self.config["--set"]["wallpaper"] = wallpaper_id
        
        # Detener el engine anterior
        self.stop_engine()
        
        # Actualizar el pool si es necesario
        if item_list is not None and current_view is not None:
            self.update_pool(item_list, current_view)
        
        # Construir los argumentos
        args = [self.script_path] + build_args(self.config)
        self.log(f"[GUI] Executing: {' '.join(args)}")
        
        # Ejecutar el script
        proc = Popen(args, stdout=PIPE, stderr=PIPE, text=True)
        
        def read_backend_output():
            for line in proc.stdout:
                self.log("[BACKEND] " + line.strip())
            for line in proc.stderr:
                self.log("[BACKEND ERROR] " + line.strip())
        
        Thread(target=read_backend_output, daemon=True).start()
    
    def apply_wallpaper(self, wallpaper_id, item_list=None, current_view=None, above=None):
        """Aplica un wallpaper específico"""
        # Configurar para modo --set
        self.config["--set"]["active"] = True
        self.config["--set"]["wallpaper"] = wallpaper_id
        self.config["--random"] = False
        self.config["--delay"]["active"] = False
        
        # Configurar el flag --above si se proporciona
        if above is not None:
            self.config["--above"] = above
        
        self.log(f"[GUI] Applying wallpaper: {wallpaper_id}")
        self.log(f"[GUI] --above flag status: {self.config.get('--above', False)}")
        
        # Ejecutar
        self.run_engine(item_list, current_view)