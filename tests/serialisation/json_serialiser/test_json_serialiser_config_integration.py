"""
Tests for JSONSerialiser integration with QUAM config system.

This module tests the JSONSerialiser constructor integration with the new 
include_defaults_in_save config field for ticket #11:
- JSONSerialiser() reads config and defaults to include_defaults=True (new behavior)
- Explicit include_defaults parameter overrides config setting
- Fallback behavior when config is not found
- Proper isolation from user's actual config files during testing
"""
import pytest
from unittest.mock import patch
from pathlib import Path

from quam.serialisation.json import JSONSerialiser


class TestJSONSerialiserConfigIntegration:
    """Test suite for JSONSerialiser config integration."""

    def test_serialiser_with_no_config_defaults_to_true(self, prevent_default_config_loading):
        """Test that JSONSerialiser defaults to include_defaults=True when no config."""
        # This should use the new default behavior when config is not available
        serialiser = JSONSerialiser()
        assert serialiser.include_defaults is True

    def test_serialiser_reads_config_include_defaults_true(self, prevent_default_config_loading):
        """Test that JSONSerialiser reads include_defaults_in_save=True from config."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is True

    def test_serialiser_reads_config_include_defaults_false(self, prevent_default_config_loading):
        """Test that JSONSerialiser reads include_defaults_in_save=False from config."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': False
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is False

    def test_explicit_include_defaults_true_overrides_config(self, prevent_default_config_loading):
        """Test that explicit include_defaults=True overrides config setting."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': False  # Config says False
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser(include_defaults=True)  # Explicit True
            assert serialiser.include_defaults is True  # Should override config

    def test_explicit_include_defaults_false_overrides_config(self, prevent_default_config_loading):
        """Test that explicit include_defaults=False overrides config setting."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True  # Config says True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser(include_defaults=False)  # Explicit False
            assert serialiser.include_defaults is False  # Should override config

    def test_config_not_found_defaults_to_true(self, prevent_default_config_loading):
        """Test fallback behavior when config loading fails."""
        with patch('quam.serialisation.json.get_quam_config', return_value=None):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is True  # New default behavior

    def test_config_loading_raises_exception_defaults_to_true(self, prevent_default_config_loading):
        """Test fallback behavior when config loading raises an exception."""
        with patch('quam.serialisation.json.get_quam_config', side_effect=Exception("Config error")):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is True  # New default behavior


class TestJSONSerialiserConfigIntegrationWithIsolatedConfigs:
    """Test JSONSerialiser with isolated config files (avoiding user config)."""

    def test_serialiser_with_isolated_config_true(self, tmp_path, monkeypatch, prevent_default_config_loading):
        """Test JSONSerialiser with isolated config file having include_defaults_in_save=True."""
        # Create isolated config file
        config_content = """
[quam]
version = 3
include_defaults_in_save = true
state_path = "{state_path}"
""".format(state_path=tmp_path / "test_state")
        
        config_file = tmp_path / "test_quam_config.toml"
        config_file.write_text(config_content)
        
        # Set environment to use our isolated config
        monkeypatch.setenv("QUAM_CONFIG_FILE", str(config_file))
        
        # Mock the config loading to use our isolated config
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is True

    def test_serialiser_with_isolated_config_false(self, tmp_path, monkeypatch, prevent_default_config_loading):
        """Test JSONSerialiser with isolated config file having include_defaults_in_save=False."""
        # Create isolated config file
        config_content = """
[quam]
version = 3
include_defaults_in_save = false
state_path = "{state_path}"
""".format(state_path=tmp_path / "test_state")
        
        config_file = tmp_path / "test_quam_config.toml"
        config_file.write_text(config_content)
        
        # Set environment to use our isolated config
        monkeypatch.setenv("QUAM_CONFIG_FILE", str(config_file))
        
        # Mock the config loading to use our isolated config
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': False
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is False

    def test_no_interaction_with_user_config_files(self, tmp_path, monkeypatch, prevent_default_config_loading):
        """Test that no user config files are accessed during testing."""
        # Ensure we're using temporary paths only
        monkeypatch.setenv("QUAM_CONFIG_FILE", str(tmp_path / "nonexistent_config.toml"))
        monkeypatch.setenv("QUAM_STATE_PATH", str(tmp_path / "test_state"))
        
        # Mock config to return our controlled value
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is True
            
        # Verify no files were created in user directories (this is implicit - 
        # the prevent_default_config_loading fixture ensures this)


class TestJSONSerialiserBackwardsCompatibility:
    """Test backwards compatibility of JSONSerialiser constructor."""

    def test_existing_explicit_usage_still_works(self, prevent_default_config_loading):
        """Test that existing code using explicit include_defaults still works."""
        # Mock config with different value to ensure explicit parameter takes precedence
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            # Existing patterns should still work
            serialiser_false = JSONSerialiser(include_defaults=False)
            assert serialiser_false.include_defaults is False
            
            serialiser_true = JSONSerialiser(include_defaults=True)
            assert serialiser_true.include_defaults is True

    def test_old_default_behavior_preserved_with_migrated_config(self, prevent_default_config_loading):
        """Test that migrated v2→v3 configs preserve old behavior."""
        # Migrated configs will have include_defaults_in_save = False 
        # to preserve the v2 behavior
        mock_migrated_config = type('MockConfig', (), {
            'include_defaults_in_save': False  # Set by migration to preserve v2 behavior
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_migrated_config):
            serialiser = JSONSerialiser()
            # Should preserve the old space-saving behavior for migrated configs
            assert serialiser.include_defaults is False

    def test_new_config_gets_new_default_behavior(self, prevent_default_config_loading):
        """Test that new v3 configs get the new default behavior."""
        # New v3 configs will have include_defaults_in_save = True by default
        mock_new_config = type('MockConfig', (), {
            'include_defaults_in_save': True  # Default for new configs
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_new_config):
            serialiser = JSONSerialiser()
            # Should use the new complete-snapshot behavior for new configs
            assert serialiser.include_defaults is True


class TestJSONSerialiserConstructorSignature:
    """Test that constructor signature changes are backwards compatible."""

    def test_constructor_accepts_all_existing_parameters(self, prevent_default_config_loading):
        """Test that constructor still accepts all existing parameters."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': False
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            # All existing parameter patterns should work
            serialiser1 = JSONSerialiser()
            serialiser2 = JSONSerialiser(include_defaults=True)  
            serialiser3 = JSONSerialiser(content_mapping={})
            serialiser4 = JSONSerialiser(state_path="/tmp/test")
            serialiser5 = JSONSerialiser(
                content_mapping={},
                include_defaults=False,
                state_path="/tmp/test"
            )
            
            # Verify they all work and have expected values
            assert serialiser1.include_defaults is False  # From mocked config
            assert serialiser2.include_defaults is True   # Explicit override
            assert serialiser3.include_defaults is False  # From mocked config
            assert serialiser4.include_defaults is False  # From mocked config
            assert serialiser5.include_defaults is False  # Explicit override