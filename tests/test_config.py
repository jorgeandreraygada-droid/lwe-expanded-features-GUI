#!/usr/bin/env python3
"""
Unit tests for Linux Wallpaper Engine GUI - Configuration Module

Tests the config.py module which handles:
- Configuration loading and saving
- Argument building for the backend script
- Directory validation
- Flag management
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add source directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gui.config import (
    load_config,
    save_config,
    merge_config,
    validate_directory,
    build_args,
    DEFAULT_CONFIG,
    update_set_flag
)


class TestConfigLoading:
    """Test configuration loading functionality"""
    
    def test_load_config_default_when_file_missing(self):
        """Should return DEFAULT_CONFIG when config file doesn't exist"""
        with patch('gui.config.path.exists', return_value=False):
            config = load_config()
            assert config == DEFAULT_CONFIG
    
    def test_load_config_from_file(self, tmp_path):
        """Should load configuration from JSON file"""
        config_file = tmp_path / "config.json"
        test_config = DEFAULT_CONFIG.copy()
        test_config["--above"] = True
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        with patch('gui.config.CONFIG_PATH', str(config_file)):
            loaded = load_config()
            assert loaded["--above"] == True
    
    def test_load_config_handles_corrupt_json(self, tmp_path):
        """Should return DEFAULT_CONFIG when JSON is corrupt"""
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        with patch('gui.config.CONFIG_PATH', str(config_file)):
            config = load_config()
            assert config == DEFAULT_CONFIG
    
    def test_load_config_returns_copy(self):
        """Should return a copy, not reference to DEFAULT_CONFIG"""
        with patch('gui.config.path.exists', return_value=False):
            config = load_config()
            config["--above"] = not config["--above"]
            # Verify DEFAULT_CONFIG wasn't modified
            assert DEFAULT_CONFIG["--above"] != config["--above"]


class TestConfigSaving:
    """Test configuration saving functionality"""
    
    def test_save_config_creates_file(self, tmp_path):
        """Should create config file if it doesn't exist"""
        config_file = tmp_path / "config.json"
        test_config = DEFAULT_CONFIG.copy()
        
        with patch('gui.config.CONFIG_PATH', str(config_file)):
            with patch('gui.config.makedirs'):
                save_config(test_config)
        
        # Verify file was written
        assert config_file.exists()
    
    def test_save_config_preserves_format(self, tmp_path):
        """Should save config as properly formatted JSON"""
        config_file = tmp_path / "config.json"
        test_config = DEFAULT_CONFIG.copy()
        test_config["--above"] = True
        test_config["--random"] = False
        
        with patch('gui.config.CONFIG_PATH', str(config_file)):
            with patch('gui.config.makedirs'):
                save_config(test_config)
        
        with open(config_file, 'r') as f:
            loaded = json.load(f)
            assert loaded["--above"] == True
            assert loaded["--random"] == False


class TestMergeConfig:
    """Test configuration merging"""
    
    def test_merge_simple_values(self):
        """Should merge simple config values"""
        defaults = {"a": 1, "b": 2}
        loaded = {"b": 20, "c": 30}
        merge_config(defaults, loaded)
        
        assert defaults["a"] == 1
        assert defaults["b"] == 20
        assert defaults["c"] == 30
    
    def test_merge_nested_dicts(self):
        """Should recursively merge nested dictionaries"""
        defaults = {
            "flags": {"a": 1, "b": 2},
            "other": {"x": 10}
        }
        loaded = {
            "flags": {"b": 20, "c": 30},
            "other": {"y": 20}
        }
        merge_config(defaults, loaded)
        
        assert defaults["flags"]["a"] == 1
        assert defaults["flags"]["b"] == 20
        assert defaults["flags"]["c"] == 30
        assert defaults["other"]["x"] == 10
        assert defaults["other"]["y"] == 20
    
    def test_merge_overwrites_types(self):
        """Should overwrite when types differ"""
        defaults = {"value": [1, 2, 3]}
        loaded = {"value": "string"}
        merge_config(defaults, loaded)
        
        assert defaults["value"] == "string"


class TestValidateDirectory:
    """Test directory validation"""
    
    def test_validate_nonexistent_directory(self):
        """Should fail for non-existent directory"""
        is_valid, error = validate_directory("/nonexistent/path")
        assert is_valid == False
        assert "does not exist" in error
    
    def test_validate_file_not_directory(self, tmp_path):
        """Should fail when path is a file, not directory"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        is_valid, error = validate_directory(str(test_file))
        assert is_valid == False
        assert "not a directory" in error
    
    def test_validate_unreadable_directory(self, tmp_path):
        """Should fail when directory is not readable"""
        test_dir = tmp_path / "readonly"
        test_dir.mkdir()
        
        with patch('os.access', return_value=False):
            is_valid, error = validate_directory(str(test_dir))
            assert is_valid == False
            assert "not readable" in error
    
    def test_validate_valid_directory(self, tmp_path):
        """Should succeed for valid directory"""
        test_dir = tmp_path / "valid"
        test_dir.mkdir()
        
        is_valid, error = validate_directory(str(test_dir))
        assert is_valid == True
        assert error is None
    
    def test_validate_empty_path(self):
        """Should fail for empty path"""
        is_valid, error = validate_directory("")
        assert is_valid == False
        assert "not specified" in error
    
    def test_validate_with_logging_callback(self, tmp_path, capsys):
        """Should call logging callback when provided"""
        callback = MagicMock()
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        validate_directory(str(test_dir), log_callback=callback)
        callback.assert_not_called()  # No warnings for valid directory
        
        # Test with invalid directory
        callback.reset_mock()
        validate_directory("/invalid", log_callback=callback)
        callback.assert_called()


class TestBuildArgs:
    """Test argument building for backend script"""
    
    def test_build_args_empty_config(self):
        """Should handle empty configuration"""
        config = {"--dir": None}
        args = build_args(config)
        assert len(args) == 0
    
    def test_build_args_with_directory(self, tmp_path):
        """Should include directory when valid"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {"--dir": str(test_dir)}
        args = build_args(config)
        
        assert "--dir" in args
        assert str(test_dir) in args
    
    def test_build_args_invalid_directory_skipped(self):
        """Should skip invalid directory"""
        config = {"--dir": "/nonexistent"}
        args = build_args(config)
        
        assert "--dir" not in args
    
    def test_build_args_above_flag(self, tmp_path):
        """Should include --above when enabled"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--above": True
        }
        args = build_args(config)
        
        assert "--above" in args
    
    def test_build_args_window_resolution(self, tmp_path):
        """Should include window resolution when active"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--window": {
                "active": True,
                "res": "0x0x1920x1080"
            }
        }
        args = build_args(config)
        
        assert "--window" in args
        assert "0x0x1920x1080" in args
    
    def test_build_args_random_flag(self, tmp_path):
        """Should include --random when enabled"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--random": True
        }
        args = build_args(config)
        
        assert "--random" in args
    
    def test_build_args_delay_flag(self, tmp_path):
        """Should include --delay with timer value"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--delay": {
                "active": True,
                "timer": "10"
            }
        }
        args = build_args(config)
        
        assert "--delay" in args
        assert "10" in args
    
    def test_build_args_set_command(self, tmp_path):
        """Should include --set with wallpaper ID"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--set": {
                "active": True,
                "wallpaper": "my_wallpaper"
            }
        }
        args = build_args(config)
        
        assert "--set" in args
        assert "my_wallpaper" in args
    
    def test_build_args_pool_items(self, tmp_path):
        """Should include --pool with wallpaper items"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--pool": ["wallpaper1", "wallpaper2", "wallpaper3"]
        }
        args = build_args(config)
        
        assert "--pool" in args
        assert "wallpaper1" in args
        assert "wallpaper2" in args
    
    def test_build_args_sound_flags(self, tmp_path):
        """Should include sound flags when configured"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--sound": {
                "silent": True,
                "noautomute": False,
                "no_audio_processing": True
            }
        }
        args = build_args(config)
        
        assert "--sound" in args
        assert "--silent" in args
        assert "--no-audio-processing" in args
    
    def test_build_args_order(self, tmp_path):
        """Should build args in correct order"""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        
        config = {
            "--dir": str(test_dir),
            "--above": True,
            "--window": {
                "active": True,
                "res": "0x0x1920x1080"
            },
            "--random": True
        }
        args = build_args(config)
        
        # --dir should come first
        assert args.index("--dir") < args.index("--above")
        # --above should come before command
        assert args.index("--above") < args.index("--random")


class TestUpdateSetFlag:
    """Test the update_set_flag function"""
    
    def test_update_set_flag_random_active(self):
        """Should clear --set when --random is active"""
        config = {
            "--random": True,
            "--delay": {"active": False},
            "--set": {"active": True, "wallpaper": "test"},
            "--dir": "/test"
        }
        update_set_flag(config)
        
        assert config["--set"]["active"] == False
        assert config["--set"]["wallpaper"] == ""
    
    def test_update_set_flag_delay_active(self):
        """Should clear --set when --delay is active"""
        config = {
            "--random": False,
            "--delay": {"active": True, "timer": "10"},
            "--set": {"active": True, "wallpaper": "test"},
            "--dir": "/test"
        }
        update_set_flag(config)
        
        assert config["--set"]["active"] == False
        assert config["--set"]["wallpaper"] == ""
    
    def test_update_set_flag_with_directory(self):
        """Should set wallpaper ID from directory when no random/delay"""
        config = {
            "--random": False,
            "--delay": {"active": False},
            "--set": {"active": False, "wallpaper": ""},
            "--dir": "/path/to/my_wallpaper"
        }
        update_set_flag(config)
        
        assert config["--set"]["active"] == True
        assert config["--set"]["wallpaper"] == "my_wallpaper"
    
    def test_update_set_flag_without_directory(self):
        """Should handle missing directory gracefully"""
        config = {
            "--random": False,
            "--delay": {"active": False},
            "--set": {"active": False, "wallpaper": ""},
            "--dir": None
        }
        update_set_flag(config)
        
        # Should not crash
        assert config["--set"]["active"] == False


class TestDefaultConfig:
    """Test the DEFAULT_CONFIG structure"""
    
    def test_default_config_structure(self):
        """Should have all required configuration keys"""
        required_keys = {
            "--window", "--dir", "--above", "--delay",
            "--random", "--set", "--sound", "--favorites",
            "--groups", "--pool"
        }
        assert required_keys.issubset(DEFAULT_CONFIG.keys())
    
    def test_default_config_immutable(self):
        """DEFAULT_CONFIG should not be modified by tests"""
        original = DEFAULT_CONFIG.copy()
        # Run some operations that might modify it
        test_config = load_config()
        # Verify DEFAULT_CONFIG unchanged
        assert DEFAULT_CONFIG == original


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
