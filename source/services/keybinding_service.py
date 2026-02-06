"""Keybinding service for executing keybinded actions via traditional Linux keyboard handling"""

from models.keybindings import KeybindingManager, KeybindingAction
from typing import Callable, Dict, Optional, List
import threading


class KeybindingService:
    """
    Service for handling keybindings and executing associated actions.
    
    Uses traditional Linux keyboard handling via Tkinter's key binding mechanism,
    rather than system-wide hotkeys.
    """
    
    def __init__(self, config: Dict, log_callback: Callable = None):
        """
        Initialize the keybinding service.
        
        Args:
            config: Configuration dictionary
            log_callback: Optional logging callback
        """
        self.config = config
        self.log = log_callback or (lambda msg: None)
        
        # Load keybindings from config
        # If --keybindings key exists in config, use it (even if empty)
        # Otherwise create a manager with no defaults
        if "--keybindings" in config:
            keybinding_data = config.get("--keybindings", {})
            self.keybinding_manager = KeybindingManager.from_dict(keybinding_data)
        else:
            # Create empty manager (no defaults)
            manager = KeybindingManager()
            manager.bindings = []
            self.keybinding_manager = manager
        
        # Action handlers - will be registered by the GUI
        self.action_handlers: Dict[KeybindingAction, Callable] = {}
    
    def register_action_handler(
        self,
        action: KeybindingAction,
        handler: Callable
    ) -> None:
        """
        Register a handler for a specific action.
        
        Args:
            action: The action to handle
            handler: Callable that will be invoked when action is triggered
        """
        self.action_handlers[action] = handler
        self.log(f"[KEYBIND] Registered handler for {action.value}")
    
    def on_key_press(self, key: str, modifiers: List[str]) -> bool:
        """
        Handle a key press event.
        
        Args:
            key: The key that was pressed (e.g., 'a', 'Return')
            modifiers: List of active modifiers (e.g., ['ctrl', 'alt'])
        
        Returns:
            True if the key press was handled by a keybinding
        """
        # Find if this key press matches any keybinding
        action = self.keybinding_manager.find_action(key, modifiers)
        
        if action and action in self.action_handlers:
            self.log(f"[KEYBIND] Executing action: {action.value}")
            try:
                # Execute in a separate thread to avoid blocking the UI
                handler = self.action_handlers[action]
                thread = threading.Thread(target=handler, daemon=True)
                thread.start()
            except Exception as e:
                self.log(f"[KEYBIND ERROR] Failed to execute {action.value}: {str(e)}")
            return True
        
        return False
    
    def get_keybinding_for_action(self, action: KeybindingAction) -> Optional[str]:
        """Get the keybinding string for a specific action"""
        for binding in self.keybinding_manager.get_all_bindings():
            if binding.action == action:
                return binding.get_keybind_string()
        return None
    
    def get_all_keybindings(self) -> Dict[str, str]:
        """Get all keybindings as a dict of action: keybind_string"""
        result = {}
        for binding in self.keybinding_manager.get_all_bindings():
            result[binding.action.value] = binding.get_keybind_string()
        return result
    
    def save_keybindings(self) -> None:
        """Save current keybindings to config"""
        self.config["--keybindings"] = self.keybinding_manager.to_dict()
        self.log("[KEYBIND] Keybindings saved to config")
    
    def reset_to_defaults(self) -> None:
        """Reset all keybindings to defaults"""
        self.keybinding_manager = KeybindingManager()
        self.save_keybindings()
        self.log("[KEYBIND] Keybindings reset to defaults")

