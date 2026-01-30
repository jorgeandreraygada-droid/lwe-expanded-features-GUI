#!/usr/bin/env python3
import subprocess
from pathlib import Path

# Paths
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"
SERVICE_NAME = "linux-wallpaperengine.service"
SERVICE_PATH = SYSTEMD_USER_DIR / SERVICE_NAME

# Path to your existing service.sh script and template
SCRIPT_DIR = Path(__file__).parent.absolute()
SERVICE_SCRIPT = SCRIPT_DIR / "startup_handler.sh"
SERVICE_TEMPLATE_FILE = SCRIPT_DIR / "startup_service.template"


def load_service_template():
    """Load the service template from file and substitute paths"""
    try:
        template = SERVICE_TEMPLATE_FILE.read_text()
        return template.replace("%SCRIPT_PATH%", str(SERVICE_SCRIPT))
    except FileNotFoundError:
        raise FileNotFoundError(f"Service template not found: {SERVICE_TEMPLATE_FILE}")


def is_service_enabled():
    """Check if the systemd service is enabled"""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-enabled", SERVICE_NAME],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def create_service_file():
    """Create the systemd service file"""
    try:
        if not SERVICE_SCRIPT.exists():
            return False, f"Service script not found: {SERVICE_SCRIPT}"
        
        SERVICE_SCRIPT.chmod(0o755)
        service_content = load_service_template()
        SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
        SERVICE_PATH.write_text(service_content)
        return True, "Service file created successfully"
    except Exception as e:
        return False, f"Failed to create service file: {e}"


def enable_startup():
    """Enable the systemd service"""
    try:
        success, message = create_service_file()
        if not success:
            return False, message
        
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            ["systemctl", "--user", "enable", SERVICE_NAME],
            check=True,
            capture_output=True
        )
        
        return True, "Startup enabled successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to enable startup: {e.stderr.decode()}"
    except Exception as e:
        return False, f"Failed to enable startup: {e}"


def disable_startup():
    """Disable the systemd service"""
    try:
        subprocess.run(
            ["systemctl", "--user", "disable", SERVICE_NAME],
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            ["systemctl", "--user", "stop", SERVICE_NAME],
            capture_output=True
        )
        
        return True, "Startup disabled successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to disable startup: {e.stderr.decode()}"
    except Exception as e:
        return False, f"Failed to disable startup: {e}"


def remove_service_file():
    """Remove the systemd service file (optional cleanup)"""
    try:
        if SERVICE_PATH.exists():
            SERVICE_PATH.unlink()
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True
        )
        return True, "Service file removed"
    except Exception as e:
        return False, f"Failed to remove service file: {e}"