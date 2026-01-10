"""
Utility functions for path resolution in different environments
Handles both native and Flatpak installations
"""
import os


def get_script_path(script_name):
    """
    Get path to backend script, Flatpak-aware
    
    Tries multiple locations:
    1. LWE_SCRIPT_DIR environment variable
    2. Relative to GUI module (native installation)
    3. /app/share/lwe-gui (Flatpak installation)
    
    Args:
        script_name: Name of script (e.g., "main.sh")
    
    Returns:
        str: Full path to script
    
    Raises:
        FileNotFoundError: If script not found in any location
    """
    
    # Try environment variable first (for custom installations)
    if os.getenv('LWE_SCRIPT_DIR'):
        script_path = os.path.join(os.getenv('LWE_SCRIPT_DIR'), script_name)
        if os.path.exists(script_path):
            return script_path
    
    # Try relative to this module (native installation)
    module_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(module_dir, "..", "..", "core", script_name)
    script_path = os.path.abspath(script_path)
    
    if os.path.exists(script_path):
        return script_path
    
    # Try /app/share/lwe-gui (Flatpak installation)
    flatpak_path = os.path.join("/app/share/lwe-gui/source/core", script_name)
    if os.path.exists(flatpak_path):
        return flatpak_path
    
    # Provide helpful error message
    attempted_paths = [
        os.getenv('LWE_SCRIPT_DIR', '<not set>'),
        script_path,
        flatpak_path
    ]
    raise FileNotFoundError(
        f"Script '{script_name}' not found in any expected location.\n"
        f"Attempted paths:\n" + "\n".join(f"  - {p}" for p in attempted_paths)
    )
