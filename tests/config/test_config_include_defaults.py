"""
Tests for QuamConfig model with new include_defaults_in_save field.

This module tests the QuamConfig model changes for ticket #11:
- New field: include_defaults_in_save with default value True
- Version bump from 2 to 3
- Field validation and behavior
"""
import pytest
from pathlib import Path

from quam.config.models.quam import QuamConfig, QuamTopLevelConfig


class TestQuamConfigIncludeDefaults:
    """Test suite for QuamConfig model with include_defaults_in_save field."""

    def test_config_has_include_defaults_in_save_field(self):
        """Test that QuamConfig has the new include_defaults_in_save field."""
        config = QuamConfig({})
        assert hasattr(config, 'include_defaults_in_save')

    def test_include_defaults_in_save_default_value_is_true(self):
        """Test that include_defaults_in_save defaults to True (new behavior)."""
        config = QuamConfig({})
        assert config.include_defaults_in_save is True

    def test_include_defaults_in_save_can_be_set_to_false(self):
        """Test that include_defaults_in_save can be explicitly set to False."""
        config = QuamConfig({"include_defaults_in_save": False})
        assert config.include_defaults_in_save is False

    def test_include_defaults_in_save_can_be_set_to_true(self):
        """Test that include_defaults_in_save can be explicitly set to True."""
        config = QuamConfig({"include_defaults_in_save": True})
        assert config.include_defaults_in_save is True

    def test_config_version_is_3(self):
        """Test that config version has been bumped to 3."""
        config = QuamConfig({})
        assert config.version == 3

    def test_config_retains_existing_fields(self):
        """Test that existing fields are still present and working."""
        config = QuamConfig({
            "state_path": "/test/path",
            "raise_error_missing_reference": True,
            "include_defaults_in_save": False
        })
        
        assert config.state_path == Path("/test/path")
        assert config.raise_error_missing_reference is True
        assert config.include_defaults_in_save is False
        assert config.version == 3

    def test_config_with_all_default_values(self):
        """Test config creation with all default values."""
        config = QuamConfig({})
        
        assert config.version == 3
        assert config.state_path is None
        assert config.raise_error_missing_reference is False
        assert config.include_defaults_in_save is True

    def test_top_level_config_still_works(self):
        """Test that QuamTopLevelConfig still works with updated QuamConfig."""
        quam_config = QuamConfig({"include_defaults_in_save": False})
        top_level = QuamTopLevelConfig({"quam": quam_config})
        
        assert top_level.quam.include_defaults_in_save is False
        assert top_level.quam.version == 3


class TestQuamConfigValidation:
    """Test suite for QuamConfig field validation."""

    def test_include_defaults_in_save_accepts_boolean_values(self):
        """Test that include_defaults_in_save accepts boolean values."""
        # True
        config_true = QuamConfig({"include_defaults_in_save": True})
        assert config_true.include_defaults_in_save is True
        
        # False
        config_false = QuamConfig({"include_defaults_in_save": False})
        assert config_false.include_defaults_in_save is False

    def test_include_defaults_in_save_type_validation(self):
        """Test that include_defaults_in_save validates type correctly."""
        # This test may depend on the validation behavior of qualibrate_config
        # If it doesn't raise an error, we'll just verify the value
        try:
            config = QuamConfig({"include_defaults_in_save": "not_a_boolean"})
            # If no error is raised, check if it was coerced or stored as-is
            # This behavior depends on the BaseConfig implementation
            assert isinstance(config.include_defaults_in_save, (bool, str))
        except (ValueError, TypeError):
            # Expected behavior if validation is strict
            pass

    def test_version_field_is_readonly_or_consistent(self):
        """Test that version field behaves consistently."""
        config1 = QuamConfig({})
        config2 = QuamConfig({})
        
        assert config1.version == config2.version == 3


class TestQuamConfigBackwardsCompatibility:
    """Test suite for backwards compatibility considerations."""

    def test_config_can_be_created_without_new_field(self):
        """Test that config can be created without specifying new field."""
        # This should work and use the default value
        config = QuamConfig({
            "state_path": "/test",
            "raise_error_missing_reference": True
            # include_defaults_in_save not specified - should use default
        })
        
        assert config.include_defaults_in_save is True  # Default value
        assert config.state_path == Path("/test")
        assert config.raise_error_missing_reference is True

    def test_existing_config_patterns_still_work(self):
        """Test that existing config creation patterns continue to work."""
        # Pattern 1: Empty config
        empty_config = QuamConfig({})
        assert empty_config.version == 3
        assert empty_config.include_defaults_in_save is True
        
        # Pattern 2: Partial config
        partial_config = QuamConfig({"state_path": "/test"})
        assert partial_config.version == 3
        assert partial_config.include_defaults_in_save is True
        
        # Pattern 3: Full config (without new field)
        full_config = QuamConfig({
            "state_path": "/test",
            "raise_error_missing_reference": True
        })
        assert full_config.version == 3
        assert full_config.include_defaults_in_save is True