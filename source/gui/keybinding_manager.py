"""
GUI-level keybinding manager for integration with the application.

NOTE: This module uses traditional Linux keyboard handling.
The systemwide keyboard listener (pynput) has been removed.

For keyboard shortcut management, you can either:
1. Use the KeybindingController (this module) - existing approach
2. Use KeyboardShortcutAPI (services.keybinding_api) - recommended new clean API

The KeyboardShortcutAPI provides a cleaner, more explicit interface.
See KEYBOARD_API_GUIDE.md for detailed documentation.
"""

from tkinter import Tk, filedialog, messagebox
from models.keybindings import KeybindingAction
from services.keybinding_service import KeybindingService
from models.config import ConfigManager
from typing import Callable, Dict, Any


class KeybindingController:
    """
    Manages keybinding integration in the GUI.
    Handles key press events and executes corresponding actions.
    """
    
    def __init__(
        self,
        main_window: Tk,
        config: Dict,
        engine_controller,  # EngineController instance
        event_handlers,     # EventHandlers instance
        gallery_view,       # GalleryView instance
        log_callback: Callable = None
    ):
        """
        Initialize the keybinding controller.
        
        Args:
            main_window: The root Tk window
            config: Configuration dictionary
            engine_controller: Instance of EngineController
            event_handlers: Instance of EventHandlers
            gallery_view: Instance of GalleryView
            log_callback: Optional logging callback
        """
        self.main_window = main_window
        self.config = config
        self.engine_controller = engine_controller
        self.event_handlers = event_handlers
        self.gallery_view = gallery_view
        self.log = log_callback or (lambda msg: None)
        
        # Create the keybinding service
        self.keybinding_service = KeybindingService(config, log_callback)
        
        # Register all action handlers
        self._register_action_handlers()
        
        # Bind the key press event on the main window
        self._setup_key_bindings()
        
        self.log("[KEYBIND] KeybindingController initialized")
    
    def _register_action_handlers(self) -> None:
        """Register handlers for all keybinding actions"""
        
        # Engine controls
        self.keybinding_service.register_action_handler(
            KeybindingAction.RUN_CURRENT_CONFIG,
            self._action_run_current_config
        )
        
        self.keybinding_service.register_action_handler(
            KeybindingAction.STOP_ENGINE,
            self._action_stop_engine
        )
        
        # Wallpaper selection
        self.keybinding_service.register_action_handler(
            KeybindingAction.SET_WALLPAPER,
            self._action_set_wallpaper
        )
        
        self.keybinding_service.register_action_handler(
            KeybindingAction.SELECT_RANDOM,
            self._action_select_random
        )
        
        # Mode toggles
        self.keybinding_service.register_action_handler(
            KeybindingAction.TOGGLE_RANDOM_MODE,
            self._action_toggle_random_mode
        )
        
        self.keybinding_service.register_action_handler(
            KeybindingAction.TOGGLE_DELAY_MODE,
            self._action_toggle_delay_mode
        )
        
        self.keybinding_service.register_action_handler(
            KeybindingAction.TOGGLE_WINDOW_MODE,
            self._action_toggle_window_mode
        )
        
        self.keybinding_service.register_action_handler(
            KeybindingAction.TOGGLE_ABOVE,
            self._action_toggle_above
        )
        
        # Navigation
        self.keybinding_service.register_action_handler(
            KeybindingAction.NEXT_WALLPAPER,
            self._action_next_wallpaper
        )
        
        self.keybinding_service.register_action_handler(
            KeybindingAction.PREVIOUS_WALLPAPER,
            self._action_previous_wallpaper
        )
        
        self.log("[KEYBIND] All action handlers registered")
    
    def _setup_key_bindings(self) -> None:
        """Setup Tkinter key bindings on the main window"""
        # Track key presses
        self.main_window.bind("<KeyPress>", self._on_key_press)
    
    def _on_key_press(self, event) -> None:
        """
        Handle Tkinter key press events.
        
        Args:
            event: Tkinter event object
        """
        # Get the key
        key = event.keysym
        
        # Build list of active modifiers
        modifiers = []
        if event.state & 0x0004:  # Ctrl
            modifiers.append('ctrl')
        if event.state & 0x0008:  # Alt
            modifiers.append('alt')
        if event.state & 0x0001:  # Shift
            modifiers.append('shift')
        if event.state & 0x0040:  # Super/Command (varies by system)
            modifiers.append('super')
        
        # Let the service handle the key press
        self.keybinding_service.on_key_press(key, modifiers)
    
    # ========== Action Handlers ==========
    
    def _action_run_current_config(self) -> None:
        """Run the current configuration"""
        self.log("[KEYBIND] Executing: Run current config")
        
        # Check if directory is selected
        if not self.config.get("--dir"):
            self.log("[KEYBIND ACTION] No directory selected")
            messagebox.showwarning(
                "No Directory",
                "Please select a wallpaper directory first"
            )
            return
        
        self.log("[KEYBIND ACTION] Starting engine with current config")
        self.engine_controller.run_engine()
    
    def _action_stop_engine(self) -> None:
        """Stop the engine"""
        self.log("[KEYBIND] Executing: Stop engine")
        self.engine_controller.stop_engine()
        self.log("[KEYBIND ACTION] Engine stopped")
    
    def _action_set_wallpaper(self) -> None:
        """Set a specific wallpaper by opening file picker"""
        self.log("[KEYBIND] Executing: Set wallpaper")
        
        if not self.config.get("--dir"):
            self.log("[KEYBIND ACTION] No directory selected")
            messagebox.showwarning(
                "No Directory",
                "Please select a wallpaper directory first"
            )
            return
        
        # Delegate to event handler which has the UI logic
        from tkinter import filedialog
        
        # Get wallpaper folders
        wallpapers = self.gallery_view._load_wallpapers_from_directory(
            self.config.get("--dir")
        )
        
        if not wallpapers:
            messagebox.showinfo("No Wallpapers", "No wallpapers found in directory")
            return
        
        # Create a simple selection dialog
        # If galleries are available, pick the first one
        if wallpapers:
            selected = wallpapers[0]
            self.log(f"[KEYBIND ACTION] Setting wallpaper: {selected.id}")
            self.engine_controller.apply_wallpaper(
                selected.id,
                wallpapers,
                "all"
            )
    
    def _action_select_random(self) -> None:
        """Select a random wallpaper from the current set"""
        self.log("[KEYBIND] Executing: Select random wallpaper")
        
        if not self.config.get("--dir"):
            self.log("[KEYBIND ACTION] No directory selected")
            messagebox.showwarning(
                "No Directory",
                "Please select a wallpaper directory first"
            )
            return
        
        # Get all wallpapers
        try:
            wallpapers = self.gallery_view._load_wallpapers_from_directory(
                self.config.get("--dir")
            )
            
            if not wallpapers:
                messagebox.showinfo("No Wallpapers", "No wallpapers found")
                return
            
            import random
            selected = random.choice(wallpapers)
            
            self.log(f"[KEYBIND ACTION] Randomly selected wallpaper: {selected.id}")
            self.engine_controller.apply_wallpaper(
                selected.id,
                wallpapers,
                "all"
            )
        except Exception as e:
            self.log(f"[KEYBIND ACTION ERROR] {str(e)}")
            messagebox.showerror("Error", f"Failed to select random wallpaper: {str(e)}")
    
    def _action_toggle_random_mode(self) -> None:
        """Toggle random mode on/off"""
        self.log("[KEYBIND] Executing: Toggle random mode")
        
        current_state = self.config.get("--random", False)
        new_state = not current_state
        
        self.config["--random"] = new_state
        
        if new_state:
            self.config["--delay"]["active"] = False
            self.config["--set"]["active"] = False
            self.log("[KEYBIND ACTION] Random mode: ON")
        else:
            self.log("[KEYBIND ACTION] Random mode: OFF")
        
        # Update UI if flags panel is available
        try:
            if hasattr(self.event_handlers.ui.get('flags_panel'), 'random_mode'):
                self.event_handlers.ui['flags_panel'].random_mode.set(new_state)
        except:
            pass
        
        ConfigManager.save(self.config)
    
    def _action_toggle_delay_mode(self) -> None:
        """Toggle delay mode on/off"""
        self.log("[KEYBIND] Executing: Toggle delay mode")
        
        current_state = self.config.get("--delay", {}).get("active", False)
        new_state = not current_state
        
        self.config["--delay"]["active"] = new_state
        
        if new_state:
            self.config["--random"] = False
            self.config["--set"]["active"] = False
            self.log("[KEYBIND ACTION] Delay mode: ON")
        else:
            self.log("[KEYBIND ACTION] Delay mode: OFF")
        
        # Update UI if flags panel is available
        try:
            if hasattr(self.event_handlers.ui.get('flags_panel'), 'delay_mode'):
                self.event_handlers.ui['flags_panel'].delay_mode.set(new_state)
        except:
            pass
        
        ConfigManager.save(self.config)
    
    def _action_toggle_window_mode(self) -> None:
        """Toggle window mode on/off"""
        self.log("[KEYBIND] Executing: Toggle window mode")
        
        current_state = self.config.get("--window", {}).get("active", False)
        new_state = not current_state
        
        self.config["--window"]["active"] = new_state
        
        if new_state:
            self.log("[KEYBIND ACTION] Window mode: ON")
        else:
            self.log("[KEYBIND ACTION] Window mode: OFF")
        
        # Update UI if flags panel is available
        try:
            if hasattr(self.event_handlers.ui.get('flags_panel'), 'window_mode'):
                self.event_handlers.ui['flags_panel'].window_mode.set(new_state)
        except:
            pass
        
        ConfigManager.save(self.config)
    
    def _action_toggle_above(self) -> None:
        """Toggle --above flag"""
        self.log("[KEYBIND] Executing: Toggle --above flag")
        
        current_state = self.config.get("--above", False)
        new_state = not current_state
        
        self.config["--above"] = new_state
        
        if new_state:
            self.log("[KEYBIND ACTION] Always above: ON")
        else:
            self.log("[KEYBIND ACTION] Always above: OFF")
        
        # Update UI if flags panel is available
        try:
            if hasattr(self.event_handlers.ui.get('flags_panel'), 'above_flag'):
                self.event_handlers.ui['flags_panel'].above_flag.set(new_state)
        except:
            pass
        
        ConfigManager.save(self.config)
    
    def _action_next_wallpaper(self) -> None:
        """Navigate to next wallpaper in gallery"""
        self.log("[KEYBIND] Executing: Next wallpaper")
        
        try:
            if hasattr(self.gallery_view, 'scroll_to_next'):
                self.gallery_view.scroll_to_next()
                self.log("[KEYBIND ACTION] Scrolled to next wallpaper")
            else:
                self.log("[KEYBIND ACTION] Gallery navigation not available")
        except Exception as e:
            self.log(f"[KEYBIND ACTION ERROR] {str(e)}")
    
    def _action_previous_wallpaper(self) -> None:
        """Navigate to previous wallpaper in gallery"""
        self.log("[KEYBIND] Executing: Previous wallpaper")
        
        try:
            if hasattr(self.gallery_view, 'scroll_to_previous'):
                self.gallery_view.scroll_to_previous()
                self.log("[KEYBIND ACTION] Scrolled to previous wallpaper")
            else:
                self.log("[KEYBIND ACTION] Gallery navigation not available")
        except Exception as e:
            self.log(f"[KEYBIND ACTION ERROR] {str(e)}")
    
    def get_keybindings_info(self) -> Dict[str, str]:
        """Get information about all keybindings"""
        return self.keybinding_service.get_all_keybindings()
