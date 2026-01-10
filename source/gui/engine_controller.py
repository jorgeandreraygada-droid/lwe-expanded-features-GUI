from subprocess import Popen, PIPE
from threading import Thread
from os import path
from gui.config import save_config, build_args
from gui.path_utils import get_script_path
import os


class EngineController:
    """Controlador del wallpaper engine"""
    
    def __init__(self, config, log_callback=None):
        self.config = config
        self.log_callback = log_callback
        
        # Obtener ruta del script main.sh (Flatpak-aware)
        try:
            self.script_path = get_script_path("main.sh")
            self.log(f"[DEBUG] Script path resolved to: {self.script_path}")
        except FileNotFoundError as e:
            self.log(f"[ERROR] {str(e)}")
            self.script_path = None
    
    def log(self, message):
        """Envía un mensaje al callback de log si existe"""
        if self.log_callback:
            self.log_callback(message)
    
    def stop_engine(self):
        """Detiene el engine actual"""
        self.log("[GUI] Stopping previous engine...")
        
        if not self.script_path:
            self.log("[ERROR] Script path not available, cannot stop engine")
            return
        
        try:
            if not os.path.exists(self.script_path):
                self.log(f"[ERROR] Script not found at: {self.script_path}")
                return
            
            stop_proc = Popen(
                [self.script_path, "--stop"],
                stdout=PIPE,
                stderr=PIPE,
                text=True
            )
            stdout, stderr = stop_proc.communicate()
            
            if stop_proc.returncode != 0 and stderr:
                self.log(f"[ERROR] Stop engine error: {stderr}")
            else:
                self.log("[GUI] Previous engine stopped")
        except Exception as e:
            self.log(f"[ERROR] Failed to stop engine: {str(e)}")
    
    def update_pool(self, item_list, current_view):
        """Actualiza el pool de wallpapers"""
        if not (self.config["--random"] or self.config["--delay"]["active"]):
            self.config["--pool"] = []
            return
        
        if current_view != "wallpapers":
            self.config["--pool"] = []
            return
        
        self.config["--pool"] = item_list.copy()
    
    def run_engine(self, item_list=None, current_view=None, show_gui_warning=True):
        """
        Ejecuta el wallpaper engine con la configuración actual
        
        Args:
            item_list: Lista de items actuales
            current_view: Vista actual de la galería
            show_gui_warning: Si True, muestra advertencias GUI sobre directorio inválido
        """
        if not self.script_path:
            self.log("[ERROR] Cannot run engine: Script path not available")
            return
        
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
        
        # Construir los argumentos (con validación de directorio)
        args = build_args(self.config, self.log, show_gui_warning)
        
        # Si no hay argumentos (directorio inválido), no ejecutar
        if not args:
            self.log("[WARNING] Cannot execute engine: No valid directory configured")
            self.log("[INFO] Please select a valid wallpaper directory using 'PICK DIR'")
            return
        
        args = [self.script_path] + args
        self.log(f"[GUI] Executing: {' '.join(args)}")
        
        # Verificar que el script existe
        if not os.path.exists(self.script_path):
            self.log(f"[ERROR] Script not found at: {self.script_path}")
            return
        
        # Ejecutar el script
        try:
            proc = Popen(args, stdout=PIPE, stderr=PIPE, text=True)
        except Exception as e:
            self.log(f"[ERROR] Failed to start engine: {str(e)}")
            return

        
        def read_backend_output():
            for line in proc.stdout:
                self.log("[BACKEND] " + line.strip())
            for line in proc.stderr:
                self.log("[BACKEND ERROR] " + line.strip())
        
        Thread(target=read_backend_output, daemon=True).start()
    
    def apply_wallpaper(self, wallpaper_id, item_list=None, current_view=None, show_gui_warning=True):
        """
        Aplica un wallpaper específico
        
        Args:
            wallpaper_id: ID del wallpaper a aplicar
            item_list: Lista de items actuales
            current_view: Vista actual de la galería
            show_gui_warning: Si True, muestra advertencias GUI sobre directorio inválido
        """
        # Configurar para modo --set
        self.config["--set"]["active"] = True
        self.config["--set"]["wallpaper"] = wallpaper_id
        self.config["--random"] = False
        self.config["--delay"]["active"] = False
        
        self.log(f"[GUI] Applying wallpaper: {wallpaper_id}")
        self.log(f"[GUI] --above flag status: {self.config.get('--above', False)}")
        
        # Ejecutar
        self.run_engine(item_list, current_view, show_gui_warning)