"""
Traditional Linux Keyboard Shortcut API

Provides a clean, standard API for managing keyboard shortcuts using traditional
Linux keyboard handling via Tkinter's native key binding mechanism (no system-wide
hotkey interception).
"""

from typing import Callable, Dict, Optional, List, Any
from models.keybindings import KeybindingAction, Keybinding, KeyModifier


class KeyboardShortcutAPI:
    """
    Standard API for managing keyboard shortcuts using traditional Linux keyboard handling.
    
    Features:
    - Define shortcuts via configuration (key + modifiers + action)
    - Register action handlers that execute when shortcuts are triggered
    - Query current shortcut bindings
    - Modify shortcuts dynamically
    - Save/load shortcut configurations
    
    Usage Example:
        api = KeyboardShortcutAPI(config, log_callback)
        api.bind_action(KeybindingAction.RUN_CURRENT_CONFIG, 'r', ['ctrl', 'alt'])
        api.on_action_handler(KeybindingAction.RUN_CURRENT_CONFIG, my_handler_func)
        api.sync_to_window(main_window)
    """
    
    def __init__(self, config: Dict, log_callback: Callable = None):
        """
        Initialize the keyboard shortcut API.
        
        Args:
            config: Application configuration dictionary
            log_callback: Optional logging function
        """
        self.config = config
        self.log = log_callback or (lambda msg: None)
        self.bindings: Dict[KeybindingAction, Dict[str, Any]] = {}
        self.handlers: Dict[KeybindingAction, Callable] = {}
        self._bound_window = None
        
        self._load_bindings_from_config()
        self.log("[KB API] KeyboardShortcutAPI initialized")
    
    def bind_action(
        self, 
        action: KeybindingAction,
        key: str,
        modifiers: Optional[List[str]] = None
    ) -> None:
        """
        Bind a keyboard shortcut to an action.
        
        Args:
            action: The action to bind (from KeybindingAction enum)
            key: The key character (e.g., 'r', 'Return', 'F1')
            modifiers: List of modifiers (['ctrl', 'alt', 'shift', 'super'])
        
        Example:
            api.bind_action(KeybindingAction.RUN_CURRENT_CONFIG, 'r', ['ctrl', 'alt'])
        """
        modifiers = modifiers or []
        self.bindings[action] = {
            'key': key,
            'modifiers': modifiers,
            'description': action.value
        }
        self.log(f"[KB API] Bound {action.value}: {key} + {modifiers}")
        self._sync_binding_to_window(action)
    
    def unbind_action(self, action: KeybindingAction) -> None:
        """
        Remove a keyboard shortcut binding.
        
        Args:
            action: The action to unbind
        """
        if action in self.bindings:
            del self.bindings[action]
            if self._bound_window:
                self._unbind_from_window(action)
            self.log(f"[KB API] Unbound {action.value}")
    
    def on_action_handler(
        self,
        action: KeybindingAction,
        handler: Callable
    ) -> None:
        """
        Register a handler function for an action.
        
        Args:
            action: The action to handle
            handler: Callable that executes when the action is triggered
        
        Example:
            api.on_action_handler(
                KeybindingAction.RUN_CURRENT_CONFIG,
                my_function
            )
        """
        self.handlers[action] = handler
        self.log(f"[KB API] Registered handler for {action.value}")
    
    def get_binding(self, action: KeybindingAction) -> Optional[Dict[str, Any]]:
        """
        Get the current binding for an action.
        
        Returns:
            Dict with 'key' and 'modifiers', or None if not bound
        
        Example:
            binding = api.get_binding(KeybindingAction.RUN_CURRENT_CONFIG)
            # {'key': 'r', 'modifiers': ['ctrl', 'alt']}
        """
        return self.bindings.get(action)
    
    def get_binding_string(self, action: KeybindingAction) -> Optional[str]:
        """
        Get human-readable binding string for an action.
        
        Returns:
            String like "Ctrl+Alt+R", or None if not bound
        """
        binding = self.bindings.get(action)
        if not binding:
            return None
        
        parts = [m.capitalize() for m in binding['modifiers']]
        parts.append(self._format_key(binding['key']))
        return "+".join(parts)
    
    def get_all_bindings(self) -> Dict[str, str]:
        """
        Get all current bindings as human-readable strings.
        
        Returns:
            Dict mapping action names to shortcut strings
        
        Example:
            {
                'run_current_config': 'Ctrl+Alt+R',
                'stop_engine': 'Ctrl+S',
                ...
            }
        """
        result = {}
        for action, binding in self.bindings.items():
            binding_str = self.get_binding_string(action)
            if binding_str:
                result[action.value] = binding_str
        return result
    
    def sync_to_window(self, main_window) -> None:
        """
        Synchronize all bindings to a Tkinter window.
        
        This should be called when the application window is ready.
        The window will start receiving keyboard events.
        
        Args:
            main_window: The Tkinter root window
        
        Example:
            api.sync_to_window(root_window)
        """
        self._bound_window = main_window
        main_window.bind("<KeyPress>", self._on_tkinter_key_press)
        self.log(f"[KB API] Synced {len(self.bindings)} bindings to window")
    
    def save_config(self) -> None:
        """
        Save current bindings to configuration.
        
        This persists the shortcuts so they load automatically next time.
        """
        config_data = {}
        for action, binding in self.bindings.items():
            config_data[action.value] = {
                'key': binding['key'],
                'modifiers': binding['modifiers']
            }
        
        self.config["--keybindings"] = config_data
        self.log("[KB API] Bindings saved to config")
    
    def reset_to_defaults(self) -> None:
        """Reset all bindings to application defaults."""
        self.bindings.clear()
        self._load_bindings_from_config()
        
        # Re-sync if window is bound
        if self._bound_window:
            self.sync_to_window(self._bound_window)
        
        self.log("[KB API] Bindings reset to defaults")
    
    # ========== Internal Methods ==========
    
    def _load_bindings_from_config(self) -> None:
        """Load bindings from configuration."""
        self.bindings.clear()
        
        if "--keybindings" not in self.config:
            return
        
        keybindings_config = self.config.get("--keybindings", {})
        
        for action_name, binding_data in keybindings_config.items():
            try:
                action = KeybindingAction(action_name)
                self.bindings[action] = {
                    'key': binding_data.get('key'),
                    'modifiers': binding_data.get('modifiers', []),
                    'description': action_name
                }
            except ValueError:
                self.log(f"[KB API] Unknown action: {action_name}")
    
    def _on_tkinter_key_press(self, event) -> None:
        """Handle Tkinter key press events."""
        try:
            key = event.keysym
            modifiers = self._extract_modifiers(event)
            
            # Find matching binding
            for action, binding in self.bindings.items():
                if (binding['key'] == key and 
                    set(binding['modifiers']) == set(modifiers)):
                    self._execute_action(action)
                    return
        except Exception as e:
            self.log(f"[KB API ERROR] {str(e)}")
    
    def _execute_action(self, action: KeybindingAction) -> None:
        """Execute the handler for an action."""
        if action not in self.handlers:
            return
        
        try:
            handler = self.handlers[action]
            import threading
            # Run in separate thread to avoid blocking UI
            thread = threading.Thread(target=handler, daemon=True)
            thread.start()
            self.log(f"[KB API] Executed action: {action.value}")
        except Exception as e:
            self.log(f"[KB API ERROR] Failed to execute {action.value}: {str(e)}")
    
    def _sync_binding_to_window(self, action: KeybindingAction) -> None:
        """Sync a single binding to the window if it's bound."""
        if not self._bound_window:
            return
        
        binding = self.bindings.get(action)
        if not binding:
            return
        
        # Tkinter uses angle bracket notation for bindings
        # Extract current window implementation to unbind old and bind new
        self._unbind_from_window(action)
    
    def _unbind_from_window(self, action: KeybindingAction) -> None:
        """Unbind an action from the window."""
        if not self._bound_window:
            return
        
        # Get all current bindings and remove this action's bindings
        # Note: Tkinter doesn't provide a direct way to unbind by action,
        # so we re-bind all when there are changes
        pass
    
    @staticmethod
    def _extract_modifiers(event) -> List[str]:
        """Extract modifier keys from a Tkinter event."""
        modifiers = []
        if event.state & 0x0004:  # Ctrl
            modifiers.append('ctrl')
        if event.state & 0x0008:  # Alt
            modifiers.append('alt')
        if event.state & 0x0001:  # Shift
            modifiers.append('shift')
        if event.state & 0x0040:  # Super/Windows key
            modifiers.append('super')
        return modifiers
    
    @staticmethod
    def _format_key(key: str) -> str:
        """Format key name for display."""
        special_keys = {
            "Return": "Enter",
            "BackSpace": "Backspace",
            "Escape": "Esc",
            "Tab": "Tab",
            "space": "Space",
            "Up": "↑",
            "Down": "↓",
            "Left": "←",
            "Right": "→",
        }
        return special_keys.get(key, key.replace("_", " ").title())
