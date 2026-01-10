#!/usr/bin/env python3
"""
Unit tests for Linux Wallpaper Engine GUI - Engine Controller Module

Tests the engine_controller.py module which handles:
- Engine process management
- Wallpaper application
- Stop/restart functionality
- Pool updates
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, call, mock_open
from subprocess import Popen, PIPE

# Add source directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gui.engine_controller import EngineController


class TestEngineControllerInit:
    """Test EngineController initialization"""
    
    def test_init_with_valid_script(self):
        """Should initialize successfully with valid script path"""
        mock_config = {
            "--dir": "/test/path",
            "--above": False,
            "--random": False,
            "--delay": {"active": False}
        }
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config)
            assert controller.script_path == '/path/to/main.sh'
    
    def test_init_with_log_callback(self):
        """Should accept and store log callback"""
        mock_config = {"--dir": None}
        mock_callback = MagicMock()
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config, log_callback=mock_callback)
            controller.log("test message")
            mock_callback.assert_called_with("test message")
    
    def test_init_without_script_path(self):
        """Should handle missing script path gracefully"""
        mock_config = {"--dir": None}
        
        with patch('gui.engine_controller.get_script_path', side_effect=FileNotFoundError("Not found")):
            controller = EngineController(mock_config)
            assert controller.script_path is None


class TestStopEngine:
    """Test engine stopping functionality"""
    
    def test_stop_engine_success(self):
        """Should successfully stop engine"""
        mock_config = {"--dir": None}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            with patch('gui.engine_controller.os.path.exists', return_value=True):
                with patch('gui.engine_controller.Popen', return_value=mock_process):
                    controller = EngineController(mock_config)
                    controller.stop_engine()
                    
                    # Verify Popen was called with correct arguments
                    mock_process.communicate.assert_called_once()
    
    def test_stop_engine_no_script_path(self):
        """Should handle missing script path gracefully"""
        mock_config = {"--dir": None}
        mock_callback = MagicMock()
        
        with patch('gui.engine_controller.get_script_path', side_effect=FileNotFoundError):
            controller = EngineController(mock_config, log_callback=mock_callback)
            controller.stop_engine()  # Should not crash
    
    def test_stop_engine_script_not_found(self):
        """Should handle when script file doesn't exist"""
        mock_config = {"--dir": None}
        mock_callback = MagicMock()
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            with patch('gui.engine_controller.os.path.exists', return_value=False):
                controller = EngineController(mock_config, log_callback=mock_callback)
                controller.stop_engine()
                # Should log error but not crash


class TestUpdatePool:
    """Test pool update functionality"""
    
    def test_update_pool_random_active(self):
        """Should update pool when --random is active"""
        mock_config = {
            "--random": True,
            "--delay": {"active": False},
            "--pool": []
        }
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config)
            items = ["item1", "item2", "item3"]
            controller.update_pool(items, "wallpapers")
            
            assert controller.config["--pool"] == items
    
    def test_update_pool_delay_active(self):
        """Should update pool when --delay is active"""
        mock_config = {
            "--random": False,
            "--delay": {"active": True, "timer": "10"},
            "--pool": []
        }
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config)
            items = ["item1", "item2"]
            controller.update_pool(items, "wallpapers")
            
            assert controller.config["--pool"] == items
    
    def test_update_pool_neither_random_nor_delay(self):
        """Should clear pool when neither random nor delay active"""
        mock_config = {
            "--random": False,
            "--delay": {"active": False},
            "--pool": ["old_item"]
        }
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config)
            controller.update_pool(["new_item"], "wallpapers")
            
            assert controller.config["--pool"] == []
    
    def test_update_pool_non_wallpapers_view(self):
        """Should clear pool for non-wallpapers views"""
        mock_config = {
            "--random": True,
            "--delay": {"active": False},
            "--pool": ["item"]
        }
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config)
            controller.update_pool(["item"], "groups")
            
            assert controller.config["--pool"] == []


class TestRunEngine:
    """Test engine execution"""
    
    def test_run_engine_no_script_path(self):
        """Should handle missing script path gracefully"""
        mock_config = {"--dir": None}
        mock_callback = MagicMock()
        
        with patch('gui.engine_controller.get_script_path', side_effect=FileNotFoundError):
            controller = EngineController(mock_config, log_callback=mock_callback)
            controller.run_engine()
            # Should log error and return
    
    def test_run_engine_success(self):
        """Should successfully run engine"""
        mock_config = {
            "--dir": "/test",
            "--above": False,
            "--random": False,
            "--delay": {"active": False},
            "--set": {"active": True, "wallpaper": "test"}
        }
        
        mock_process = MagicMock()
        mock_process.stdout = []
        mock_process.stderr = []
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            with patch('gui.engine_controller.save_config'):
                with patch('gui.engine_controller.build_args', return_value=['--dir', '/test']):
                    with patch('gui.engine_controller.os.path.exists', return_value=True):
                        with patch('gui.engine_controller.Popen', return_value=mock_process):
                            controller = EngineController(mock_config)
                            controller.run_engine()
    
    def test_run_engine_no_valid_directory(self):
        """Should handle invalid directory"""
        mock_config = {
            "--dir": None,
            "--above": False,
            "--random": False,
            "--delay": {"active": False},
            "--set": {"active": False, "wallpaper": ""}
        }
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            with patch('gui.engine_controller.save_config'):
                with patch('gui.engine_controller.build_args', return_value=[]):
                    controller = EngineController(mock_config)
                    controller.run_engine()
                    # Should return early without running


class TestApplyWallpaper:
    """Test wallpaper application"""
    
    def test_apply_wallpaper_with_item_list(self):
        """Should apply wallpaper with item list"""
        mock_config = {
            "--dir": "/test",
            "--above": False,
            "--random": False,
            "--delay": {"active": False},
            "--set": {"active": True, "wallpaper": "test"},
            "--pool": []
        }
        
        mock_process = MagicMock()
        mock_process.stdout = []
        mock_process.stderr = []
        
        items = ["item1", "item2"]
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            with patch('gui.engine_controller.save_config'):
                with patch('gui.engine_controller.build_args', return_value=['--dir', '/test']):
                    with patch('gui.engine_controller.os.path.exists', return_value=True):
                        with patch('gui.engine_controller.Popen', return_value=mock_process):
                            controller = EngineController(mock_config)
                            controller.apply_wallpaper("test_wallpaper", item_list=items, current_view="wallpapers")
                            
                            # Verify pool was updated
                            assert controller.config["--pool"] == items


class TestEngineControllerLogging:
    """Test logging functionality"""
    
    def test_log_without_callback(self):
        """Should handle logging without callback"""
        mock_config = {"--dir": None}
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config)
            controller.log("test message")  # Should not crash
    
    def test_log_with_callback(self):
        """Should call logging callback"""
        mock_config = {"--dir": None}
        mock_callback = MagicMock()
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config, log_callback=mock_callback)
            controller.log("test message")
            mock_callback.assert_called_with("test message")
    
    def test_log_multiple_messages(self):
        """Should log multiple messages"""
        mock_config = {"--dir": None}
        mock_callback = MagicMock()
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            controller = EngineController(mock_config, log_callback=mock_callback)
            
            controller.log("message1")
            controller.log("message2")
            controller.log("message3")
            
            assert mock_callback.call_count == 3


class TestEngineControllerIntegration:
    """Integration tests for engine controller"""
    
    def test_full_wallpaper_cycle(self):
        """Should handle complete wallpaper cycle: stop -> run -> apply"""
        mock_config = {
            "--dir": "/test",
            "--above": True,
            "--random": False,
            "--delay": {"active": False},
            "--set": {"active": True, "wallpaper": "test"},
            "--pool": []
        }
        
        mock_process = MagicMock()
        mock_process.stdout = []
        mock_process.stderr = []
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        
        with patch('gui.engine_controller.get_script_path', return_value='/path/to/main.sh'):
            with patch('gui.engine_controller.save_config'):
                with patch('gui.engine_controller.build_args', return_value=['--above', '--set', 'test']):
                    with patch('gui.engine_controller.os.path.exists', return_value=True):
                        with patch('gui.engine_controller.Popen', return_value=mock_process):
                            controller = EngineController(mock_config)
                            
                            # Stop previous
                            controller.stop_engine()
                            
                            # Run new engine
                            controller.run_engine()
                            
                            # Verify both operations completed
                            assert mock_process.communicate.called


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
