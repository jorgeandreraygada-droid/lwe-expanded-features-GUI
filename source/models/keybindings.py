"""Keybinding model and management"""

from enum import Enum
from typing import Dict, Any, List, Tuple


class KeybindingAction(Enum):
    """Available keybinding actions"""
    
    # Engine controls
    RUN_CURRENT_CONFIG = "run_current_config"
    STOP_ENGINE = "stop_engine"
    
    # Wallpaper selection
    SET_WALLPAPER = "set_wallpaper"
    SELECT_RANDOM = "select_random"
    
    # Mode toggles
    TOGGLE_RANDOM_MODE = "toggle_random_mode"
    TOGGLE_DELAY_MODE = "toggle_delay_mode"
    TOGGLE_WINDOW_MODE = "toggle_window_mode"
    TOGGLE_ABOVE = "toggle_above"
    
    # Navigation
    NEXT_WALLPAPER = "next_wallpaper"
    PREVIOUS_WALLPAPER = "previous_wallpaper"


class KeyModifier(Enum):
    """Key modifiers"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    SUPER = "super"  # Windows/Command key


class Keybinding:
    """Represents a single keybinding"""
    
    def __init__(
        self,
        key: str,
        action: KeybindingAction,
        modifiers: List[KeyModifier] = None,
        enabled: bool = True,
        description: str = None
    ):
        """
        Initialize a keybinding.
        
        Args:
            key: The key character (e.g., 'a', 'Return', 'F1')
            action: The action to execute
            modifiers: List of key modifiers (Ctrl, Alt, Shift, Super)
            enabled: Whether this keybinding is active
            description: Human-readable description of the keybinding
        """
        self.key = key
        self.action = action
        self.modifiers = modifiers or []
        self.enabled = enabled
        self.description = description or action.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "key": self.key,
            "action": self.action.value,
            "modifiers": [m.value for m in self.modifiers],
            "enabled": self.enabled,
            "description": self.description
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Keybinding":
        """Create from dictionary (JSON deserialization)"""
        try:
            action = KeybindingAction(data["action"])
            modifiers = [KeyModifier(m) for m in data.get("modifiers", [])]
            return Keybinding(
                key=data["key"],
                action=action,
                modifiers=modifiers,
                enabled=data.get("enabled", True),
                description=data.get("description")
            )
        except (KeyError, ValueError):
            return None
    
    def get_keybind_string(self) -> str:
        """Get human-readable keybinding string (e.g., 'Ctrl+Alt+R')"""
        parts = [m.value.capitalize() for m in self.modifiers]
        parts.append(self._format_key(self.key))
        return "+".join(parts)
    
    @staticmethod
    def _format_key(key: str) -> str:
        """Format key name for display"""
        special_keys = {
            "Return": "Enter",
            "Escape": "Esc",
            "space": "Space",
            "Tab": "Tab",
            "BackSpace": "Backspace",
        }
        return special_keys.get(key, key.upper() if len(key) == 1 else key)
    
    def matches(self, key: str, modifiers: List[str]) -> bool:
        """
        Check if this keybinding matches the given key press.
        
        Args:
            key: The key that was pressed
            modifiers: List of active modifiers (e.g., ['ctrl', 'alt'])
        
        Returns:
            True if this keybinding was triggered
        """
        if not self.enabled:
            return False
        
        if self.key != key:
            return False
        
        # Normalize modifiers to lowercase
        active_mods = set(m.lower() for m in modifiers)
        expected_mods = set(m.value.lower() for m in self.modifiers)
        
        return active_mods == expected_mods


class KeybindingManager:
    """Manages a collection of keybindings"""
    
    def __init__(self):
        self.bindings: List[Keybinding] = []
        self._setup_defaults()
    
    def _setup_defaults(self):
        """Setup default keybindings"""
        defaults = [
            Keybinding(
                "r",
                KeybindingAction.RUN_CURRENT_CONFIG,
                [KeyModifier.CTRL, KeyModifier.ALT],
                description="Run current configuration"
            ),
            Keybinding(
                "s",
                KeybindingAction.STOP_ENGINE,
                [KeyModifier.CTRL, KeyModifier.ALT],
                description="Stop the engine"
            ),
            Keybinding(
                "w",
                KeybindingAction.SET_WALLPAPER,
                [KeyModifier.CTRL, KeyModifier.ALT],
                description="Set a specific wallpaper (shows picker)"
            ),
            Keybinding(
                "d",
                KeybindingAction.SELECT_RANDOM,
                [KeyModifier.CTRL, KeyModifier.ALT],
                description="Select a random wallpaper"
            ),
            Keybinding(
                "n",
                KeybindingAction.NEXT_WALLPAPER,
                [KeyModifier.SUPER],
                description="Next wallpaper"
            ),
            Keybinding(
                "p",
                KeybindingAction.PREVIOUS_WALLPAPER,
                [KeyModifier.SUPER],
                description="Previous wallpaper"
            ),
        ]
        self.bindings = defaults
    
    def add_binding(self, binding: Keybinding) -> bool:
        """Add a new keybinding"""
        # Check for duplicates
        for existing in self.bindings:
            if (existing.key == binding.key and
                set(existing.modifiers) == set(binding.modifiers)):
                return False
        
        self.bindings.append(binding)
        return True
    
    def remove_binding(self, key: str, modifiers: List[KeyModifier]) -> bool:
        """Remove a keybinding"""
        for i, binding in enumerate(self.bindings):
            if (binding.key == key and
                set(binding.modifiers) == set(modifiers)):
                self.bindings.pop(i)
                return True
        return False
    
    def update_binding(self, old_key: str, old_modifiers: List[KeyModifier],
                      new_binding: Keybinding) -> bool:
        """Update an existing keybinding"""
        for binding in self.bindings:
            if (binding.key == old_key and
                set(binding.modifiers) == set(old_modifiers)):
                binding.key = new_binding.key
                binding.modifiers = new_binding.modifiers
                binding.action = new_binding.action
                binding.enabled = new_binding.enabled
                binding.description = new_binding.description
                return True
        return False
    
    def find_action(self, key: str, modifiers: List[str]) -> KeybindingAction:
        """Find action for a key press"""
        for binding in self.bindings:
            if binding.matches(key, modifiers):
                return binding.action
        return None
    
    def get_all_bindings(self) -> List[Keybinding]:
        """Get all keybindings"""
        return self.bindings.copy()
    
    def get_enabled_bindings(self) -> List[Keybinding]:
        """Get only enabled keybindings"""
        return [b for b in self.bindings if b.enabled]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "bindings": [b.to_dict() for b in self.bindings]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "KeybindingManager":
        """Create from dictionary (JSON deserialization)"""
        manager = KeybindingManager()
        manager.bindings = []
        
        for binding_data in data.get("bindings", []):
            binding = Keybinding.from_dict(binding_data)
            if binding:
                manager.bindings.append(binding)
        
        # Don't set defaults - if keybindings data exists (even if empty),
        # respect the user's choice to have no bindings
        return manager
    
    def enable_binding(self, key: str, modifiers: List[KeyModifier]) -> bool:
        """Enable a specific keybinding"""
        for binding in self.bindings:
            if (binding.key == key and
                set(binding.modifiers) == set(modifiers)):
                binding.enabled = True
                return True
        return False
    
    def disable_binding(self, key: str, modifiers: List[KeyModifier]) -> bool:
        """Disable a specific keybinding"""
        for binding in self.bindings:
            if (binding.key == key and
                set(binding.modifiers) == set(modifiers)):
                binding.enabled = False
                return True
        return False
