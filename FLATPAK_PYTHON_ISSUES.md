# Flatpak Python Code Analysis - Issues & Fixes

## Critical Issues Found

### 1. **CRITICAL: Script Path Resolution in Flatpak**

**Files Affected:**
- [source/gui/engine_controller.py](source/gui/engine_controller.py#L16) - Line 16
- [source/gui/event_handler/event_handler.py](source/gui/event_handler/event_handler.py#L239) - Line 239

**Problem:**
The code uses relative path traversal to find `main.sh`:
```python
# engine_controller.py line 16
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
self.script_path = os.path.join(project_root, "core", "main.sh")

# event_handler.py line 239
script_path = path.join(path.dirname(__file__), "..", "..", "core", "main.sh")
```

**Why it breaks in Flatpak:**
- In Flatpak, the GUI runs from `/app/share/lwe-gui/source/gui/gui_engine.py`
- The `__file__` attribute points to that location inside the sandbox
- Traversing up `..` directories gets `/app/share/lwe-gui/` → expects `main.sh` at `/app/share/lwe-gui/core/main.sh`
- **This is correct!** But only if script is actually there. Need to verify actual path.

**Expected path in Flatpak:**
```
/app/share/lwe-gui/source/core/main.sh  ✓
```

**Status:** Should work if manifest install is correct. Need to verify manifest copies scripts.

---

### 2. **Icon/Image Loading Failures**

**Files Affected:**
- [source/gui/wallpaper_loader.py](source/gui/wallpaper_loader.py#L40-L42) - Lines 40-42

**Problem:**
```python
img = Image.open(full_path)
img.thumbnail(THUMB_SIZE)
tk_img = ImageTk.PhotoImage(img)
```

**Why it fails in Flatpak:**
- Thumbnail is destroyed before PhotoImage can reference it
- `Image.thumbnail()` modifies in-place but doesn't hold reference
- `PhotoImage` needs image data to remain in memory
- When thumbnail goes out of scope, the image becomes invalid

**Fix:** Keep reference to PIL Image:
```python
img = Image.open(full_path)
img.thumbnail(THUMB_SIZE)
tk_img = ImageTk.PhotoImage(image=img)  # Keep reference
# Store both to prevent garbage collection
self.preview_cache[wallpaper_folder] = (img, tk_img)
```

---

### 3. **Config File Paths May Be Inaccessible**

**Files Affected:**
- [source/gui/config.py](source/gui/config.py#L9) - Lines 9-12

**Problem:**
```python
def get_config_path():
    xdg_config = getenv('XDG_CONFIG_HOME', path.expanduser('~/.config'))
    return path.join(xdg_config, 'linux-wallpaper-engine', 'config.json')
```

**Why it fails in Flatpak:**
- Flatpak redirects `~/.config` to `/home/user/.var/app/com.github.mauefrod.LWEExpandedFeaturesGUI/config`
- `path.expanduser()` correctly expands `~` to home
- But in Flatpak, the actual home might be different
- Should use `XDG_CONFIG_HOME` environment variable if set (Flatpak usually sets this)

**Status:** Should work due to `getenv()` check, but verify.

---

### 4. **Subprocess Error Handling Missing**

**Files Affected:**
- [source/gui/engine_controller.py](source/gui/engine_controller.py#L27-L31) - Lines 27-31
- [source/gui/engine_controller.py](source/gui/engine_controller.py#L88) - Line 88
- [source/gui/event_handler/event_handler.py](source/gui/event_handler/event_handler.py#L32) - Line 32
- [source/gui/event_handler/event_handler.py](source/gui/event_handler/event_handler.py#L240) - Line 240

**Problem:**
```python
# engine_controller.py line 27-31
stop_proc = Popen([self.script_path, "--stop"], stdout=PIPE, stderr=PIPE)
# No error handling if script doesn't exist or can't execute

# event_handler.py line 32
Popen(["xdg-open", self.config["--dir"]])  # No error handling

# event_handler.py line 240
proc = Popen([script_path, "--stop"])  # No error handling
```

**Why it fails in Flatpak:**
- If `main.sh` path is wrong, Popen fails silently
- `xdg-open` might not exist or work differently in Flatpak
- No error messages to logs, so user sees nothing
- Error output is captured but never read

**Fixes needed:**
1. Add try/except around Popen calls
2. Check if scripts exist before executing
3. Log stderr output to see actual errors
4. Handle FileNotFoundError gracefully

---

### 5. **Relative Path Issue in event_handler.py**

**Files Affected:**
- [source/gui/event_handler/event_handler.py](source/gui/event_handler/event_handler.py#L239) - Line 239

**Problem:**
```python
script_path = path.join(path.dirname(__file__), "..", "..", "core", "main.sh")
```

**Why it's problematic:**
- `path.dirname(__file__)` returns a relative path in some contexts
- `"..", ".."` traversal can be unpredictable
- No verification that file exists after constructing path
- Path isn't normalized

**Fix:**
```python
script_path = path.join(path.dirname(__file__), "..", "..", "core", "main.sh")
script_path = os.path.abspath(script_path)  # Add this
if not os.path.exists(script_path):
    raise FileNotFoundError(f"main.sh not found at {script_path}")
```

---

### 6. **Flatpak Data Directory Handling**

**Files Affected:**
- [source/gui/config.py](source/gui/config.py#L9-L11) - All config operations

**Problem:**
Config uses `~/.config` but doesn't handle Flatpak's restricted filesystem

**Status:** Should work due to `--filesystem=xdg-config` permission in manifest

---

## Summary of Flatpak-Specific Issues

| Issue | Severity | Type | Status |
|-------|----------|------|--------|
| Script path resolution | HIGH | Path handling | Needs verification |
| Image/Icon GC issue | MEDIUM | Memory/References | Needs fix |
| Config path access | LOW | Environment | Should work |
| Subprocess error handling | MEDIUM | Error handling | Needs implementation |
| Relative path construction | MEDIUM | Path handling | Needs fix |
| xdg-open availability | MEDIUM | External command | May work (needs testing) |

---

## Recommended Fixes

### Fix 1: Add Flatpak-aware path resolution

```python
# In a new utility module (source/gui/path_utils.py)
import os
import sys

def get_script_path(script_name):
    """Get path to backend script, Flatpak-aware"""
    
    # Try environment variable first (Flatpak might set this)
    if os.getenv('LWE_SCRIPT_DIR'):
        script_path = os.path.join(os.getenv('LWE_SCRIPT_DIR'), script_name)
        if os.path.exists(script_path):
            return script_path
    
    # Try relative to this module (normal case)
    module_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(module_dir, "..", "..", "core", script_name)
    script_path = os.path.abspath(script_path)
    
    if os.path.exists(script_path):
        return script_path
    
    # Try /app/share/lwe-gui (Flatpak installation)
    flatpak_path = os.path.join("/app/share/lwe-gui/source/core", script_name)
    if os.path.exists(flatpak_path):
        return flatpak_path
    
    raise FileNotFoundError(f"Script not found: {script_name}")
```

### Fix 2: Fix image reference issue

```python
# In wallpaper_loader.py
def load_preview(self, wallpaper_folder):
    """Carga la imagen de preview de un wallpaper"""
    if wallpaper_folder in self.preview_cache:
        return self.preview_cache[wallpaper_folder][1]  # Return PhotoImage
    
    for name in ("preview.jpg", "preview.png", "preview.gif"):
        full_path = path.join(wallpaper_folder, name)
        if path.exists(full_path):
            try:
                img = Image.open(full_path)
                img.thumbnail(THUMB_SIZE)
                tk_img = ImageTk.PhotoImage(image=img)
                # Store both PIL Image and PhotoImage to prevent garbage collection
                self.preview_cache[wallpaper_folder] = (img, tk_img)
                return tk_img
            except Exception as e:
                # Log error but don't crash
                print(f"Error loading preview {full_path}: {e}")
                continue
    return None
```

### Fix 3: Add subprocess error handling

```python
# In engine_controller.py
from subprocess import Popen, PIPE

def stop_engine(self):
    """Detiene el engine actual"""
    self.log("[GUI] Stopping previous engine...")
    try:
        if not os.path.exists(self.script_path):
            self.log(f"[ERROR] Script not found: {self.script_path}")
            return
        
        stop_proc = Popen(
            [self.script_path, "--stop"],
            stdout=PIPE,
            stderr=PIPE,
            text=True
        )
        stdout, stderr = stop_proc.communicate()
        if stderr:
            self.log(f"[ERROR] {stderr}")
    except Exception as e:
        self.log(f"[ERROR] Failed to stop engine: {e}")
```

---

## Testing in Flatpak

After fixes are applied, test with:

```bash
# Build and install
flatpak-builder build-dir flatpak/com.github.mauefrod.LWEExpandedFeaturesGUI.yml \
  --user --install --force-clean

# Run with debug output
FLATPAK_DEBUG=1 flatpak run \
  com.github.mauefrod.LWEExpandedFeaturesGUI --dir ~/wallpapers

# Check logs
tail -f ~/.local/share/linux-wallpaper-engine-features/logs.txt

# Look for:
# - Icon/preview loading errors
# - Script path resolution messages
# - Subprocess call failures
```

---

## Implementation Priority

1. **HIGH**: Fix script path resolution (Fix 1) - Core functionality depends on this
2. **MEDIUM**: Fix subprocess error handling (Fix 3) - Better debugging
3. **MEDIUM**: Fix image reference issue (Fix 2) - Prevents preview crashes

