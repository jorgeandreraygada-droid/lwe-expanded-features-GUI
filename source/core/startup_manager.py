import subprocess
import sys
from pathlib import Path
from datetime import datetime

# This file is in source/core/
SCRIPT_DIR = Path(__file__).parent.absolute()
CORE_DIR = SCRIPT_DIR  # source/core/
SOURCE_DIR = CORE_DIR.parent  # source/
GUI_DIR = SOURCE_DIR / "gui"

# Add gui directory to path for imports
sys.path.insert(0, str(GUI_DIR))

from config import load_config, build_args

# Path to log file (same as your GUI uses)
LOG_FILE = Path.home() / ".local" / "share" / "linux-wallpaper-engine-features" / "logs.txt"

def log_to_file(message):
    """Write log message to file"""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to log file: {e}")

def log(message):
    """Log to both console and file"""
    print(message)
    log_to_file(message)

def run_at_startup():
    config = load_config()
    
    log("[STARTUP] ========== Linux Wallpaper Engine Startup ==========")
    log(f"[STARTUP] Working directory: {CORE_DIR}")
    
    if not config.get("run_at_startup", False):
        log("[INFO] Run at startup is disabled")
        return
    
    log("[STARTUP] Configuration loaded:")
    log(f"[STARTUP]   Directory: {config.get('--dir', 'Not set')}")
    log(f"[STARTUP]   Window mode: {config.get('--window', {}).get('active', False)}")
    log(f"[STARTUP]   Above flag: {config.get('--above', False)}")
    log(f"[STARTUP]   Random mode: {config.get('--random', False)}")
    log(f"[STARTUP]   Delay mode: {config.get('--delay', {}).get('active', False)}")
    if config.get('--delay', {}).get('active', False):
        log(f"[STARTUP]   Delay timer: {config.get('--delay', {}).get('timer', '0')} seconds")
    log(f"[STARTUP]   Set wallpaper: {config.get('--set', {}).get('wallpaper', 'Not set')}")
    log(f"[STARTUP]   Sound silent: {config.get('--sound', {}).get('silent', False)}")
    log(f"[STARTUP]   Pool size: {len(config.get('--pool', []))} wallpapers")
    
    args = build_args(config, log_callback=log)
    
    if not args:
        log("[WARNING] No valid arguments to run")
        log("[WARNING] Please configure a valid wallpaper directory")
        return
    
    # main.sh is in source/core/
    main_script = CORE_DIR / "main.sh"
    
    # Verificar que el script existe
    if not main_script.exists():
        log(f"[ERROR] Script not found: {main_script}")
        sys.exit(1)
    
    # Verificar permisos de ejecución
    if not main_script.stat().st_mode & 0o111:
        log(f"[ERROR] Script is not executable: {main_script}")
        log(f"[ERROR] Run: chmod +x {main_script}")
        sys.exit(1)
    
    cmd = [str(main_script)] + args
    log(f"[STARTUP] Executing command: {' '.join(cmd)}")
    log("[STARTUP] =========================================================")
    
    try:
        # IMPORTANTE: Ejecutar desde el directorio correcto (CORE_DIR)
        # para que main.sh pueda encontrar sus dependencias
        result = subprocess.run(
            cmd, 
            check=True,
            capture_output=True,
            text=True,
            cwd=str(CORE_DIR)  # ← ESTA ES LA CLAVE
        )
        
        if result.stdout:
            log(f"[STARTUP] Output: {result.stdout}")
        if result.stderr:
            log(f"[STARTUP] Stderr: {result.stderr}")
            
        log("[STARTUP] Wallpaper engine started successfully")
        
    except subprocess.CalledProcessError as e:
        log(f"[ERROR] Failed to run wallpaper engine")
        log(f"[ERROR] Return code: {e.returncode}")
        if e.stdout:
            log(f"[ERROR] Stdout: {e.stdout}")
        if e.stderr:
            log(f"[ERROR] Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        log(f"[ERROR] Script not found: {main_script}")
        sys.exit(1)
    except Exception as e:
        log(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_at_startup()