#!/usr/bin/env python3
"""
Startup Manager for Linux Wallpaper Engine
Handles application startup with saved configuration
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# ==============================================================================
# PATH SETUP
# ==============================================================================

# This file is in source/core/
SCRIPT_DIR = Path(__file__).parent.absolute()
CORE_DIR = SCRIPT_DIR  # source/core/
SOURCE_DIR = CORE_DIR.parent  # source/
GUI_DIR = SOURCE_DIR / "gui"

# Verify required directories exist
if not GUI_DIR.exists():
    print(f"[FATAL ERROR] GUI directory not found: {GUI_DIR}")
    sys.exit(1)

# Add directories to path for imports (order matters - SOURCE_DIR first for proper module resolution)
sys.path.insert(0, str(SOURCE_DIR))
sys.path.insert(0, str(GUI_DIR))
sys.path.insert(0, str(CORE_DIR))

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

# Path to log file (same as GUI uses)
LOG_DIR = Path.home() / ".local" / "share" / "linux-wallpaper-engine-features"
LOG_FILE = LOG_DIR / "logs.txt"


def log_to_file(message):
    """Write log message to file"""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to log file: {e}", file=sys.stderr)


def log(message):
    """Log to both console and file"""
    print(message)
    log_to_file(message)


# ==============================================================================
# ENVIRONMENT VALIDATION
# ==============================================================================

def validate_environment():
    """Validate that required environment variables are set"""
    log("[STARTUP] Validating environment...")
    
    errors = []
    
    # Check DISPLAY is set
    if not os.environ.get("DISPLAY"):
        errors.append("DISPLAY is not set")
    
    # Check XAUTHORITY is set
    if not os.environ.get("XAUTHORITY"):
        errors.append("XAUTHORITY is not set (X11 may not be available)")
    
    # Check main.sh exists
    main_script = CORE_DIR / "main.sh"
    if not main_script.exists():
        errors.append(f"main.sh not found: {main_script}")
    
    if errors:
        log("[WARNING] Environment issues detected:")
        for error in errors:
            log(f"  - {error}")
        return False
    
    log("[STARTUP] Environment validation passed")
    return True


# ==============================================================================
# CONFIGURATION & EXECUTION
# ==============================================================================

def run_at_startup():
    """Main startup function"""
    try:
        from gui.config import load_config, build_args
    except ImportError as e:
        log(f"[FATAL ERROR] Failed to import config module: {e}")
        sys.exit(1)
    
    log("[STARTUP] ========== Linux Wallpaper Engine Startup ==========")
    log(f"[STARTUP] Working directory: {CORE_DIR}")
    log(f"[STARTUP] User: {os.environ.get('USER', 'unknown')}")
    log(f"[STARTUP] Python: {sys.version.split()[0]}")
    
    # Validate environment
    if not validate_environment():
        log("[WARNING] Some environment variables are missing, continuing anyway...")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        log(f"[ERROR] Failed to load configuration: {e}")
        sys.exit(1)
    
    log("[STARTUP] Configuration loaded successfully")
    
    # Check if startup is enabled
    if not config.get("__run_at_startup__", False):
        log("[INFO] Run at startup is disabled - exiting gracefully")
        return
    
    # Log configuration
    log("[STARTUP] Configuration details:")
    log(f"[STARTUP]   Directory: {config.get('--dir', 'Not set')}")
    log(f"[STARTUP]   Window mode: {config.get('--window', {}).get('active', False)}")
    log(f"[STARTUP]   Above flag: {config.get('--above', False)}")
    log(f"[STARTUP]   Random mode: {config.get('--random', False)}")
    log(f"[STARTUP]   Delay mode: {config.get('--delay', {}).get('active', False)}")
    if config.get('--delay', {}).get('active', False):
        log(f"[STARTUP]   Delay timer: {config.get('--delay', {}).get('timer', '0')} seconds")
    log(f"[STARTUP]   Set wallpaper: {config.get('--set', {}).get('wallpaper', 'Not set')}")
    log(f"[STARTUP]   Sound silent: {config.get('--sound', {}).get('silent', False)}")
    pool_size = len(config.get('--pool', []))
    log(f"[STARTUP]   Pool size: {pool_size} wallpapers")
    
    # Build arguments
    try:
        args = build_args(config, log_callback=log)
    except Exception as e:
        log(f"[ERROR] Failed to build arguments: {e}")
        sys.exit(1)
    
    if not args:
        log("[WARNING] No valid arguments to run")
        log("[WARNING] Please configure a valid wallpaper directory")
        return
    
    # Verify main.sh exists and is executable
    main_script = CORE_DIR / "main.sh"
    
    if not main_script.exists():
        log(f"[FATAL ERROR] Script not found: {main_script}")
        sys.exit(1)
    
    # Make it executable (in case permissions are wrong)
    try:
        mode = main_script.stat().st_mode
        if not (mode & 0o111):  # Not executable
            log(f"[INFO] Making script executable: {main_script}")
            main_script.chmod(mode | 0o111)
    except Exception as e:
        log(f"[WARNING] Failed to set executable permissions: {e}")
    
    # Build and log the command
    cmd = [str(main_script)] + args
    cmd_str = " ".join(cmd)
    log(f"[STARTUP] Executing command:")
    log(f"[STARTUP]   {cmd_str}")
    log("[STARTUP] =========================================================")
    
    # Execute the wallpaper engine
    try:
        # IMPORTANT: Execute from CORE_DIR so main.sh can find its dependencies
        result = subprocess.run(
            cmd, 
            check=False,  # Don't raise exception, we'll handle errors manually
            capture_output=True,
            text=True,
            cwd=str(CORE_DIR)
        )
        
        # Log output
        if result.stdout:
            log(f"[STARTUP] Output:\n{result.stdout}")
        if result.stderr:
            log(f"[STARTUP] Stderr:\n{result.stderr}")
        
        if result.returncode == 0:
            log("[STARTUP] Wallpaper engine started successfully")
            return
        else:
            log(f"[WARNING] Command exited with code {result.returncode}")
            log("[WARNING] This may be normal if the engine daemonizes")
            # Don't fail on non-zero exit (engine may have daemonized)
            return
            
    except subprocess.CalledProcessError as e:
        log(f"[ERROR] Failed to run wallpaper engine")
        log(f"[ERROR] Return code: {e.returncode}")
        if e.stdout:
            log(f"[ERROR] Stdout: {e.stdout}")
        if e.stderr:
            log(f"[ERROR] Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        log(f"[FATAL ERROR] Script not found: {main_script}")
        sys.exit(1)
    except Exception as e:
        log(f"[FATAL ERROR] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        log(f"[FATAL ERROR] Traceback:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_at_startup()
    except KeyboardInterrupt:
        log("[STARTUP] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"[FATAL ERROR] Unhandled exception: {e}")
        import traceback
        log(f"[FATAL ERROR] Traceback:\n{traceback.format_exc()}")
        sys.exit(1)