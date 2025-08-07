"""
Tests for config migration from version 2 to version 3.

This module tests the migration logic for ticket #11:
- Forward migration: v2 → v3 (adds include_defaults_in_save = False to preserve existing behavior)
- Backward migration: v3 → v2 (removes include_defaults_in_save field)
- Preserves all other config fields during migration
"""
import pytest
from pathlib import Path

from quam.config.cli.migrations.v2_v3 import Migrate


class TestConfigMigrationV2V3:
    """Test suite for config migration from version 2 to version 3."""

    def test_migration_class_attributes(self):
        """Test that migration class has correct version attributes."""
        assert Migrate.from_version == 2
        assert Migrate.to_version == 3

    def test_forward_migration_minimal_config(self):
        """Test forward migration v2 → v3 with minimal config data."""
        v2_data = {
            "quam": {
                "version": 2,
                "state_path": None,
                "raise_error_missing_reference": False
            }
        }
        
        v3_data = Migrate.forward(v2_data)
        
        expected = {
            "quam": {
                "version": 3,
                "state_path": None,
                "raise_error_missing_reference": False,
                "include_defaults_in_save": False  # Preserve existing behavior
            }
        }
        assert v3_data == expected

    def test_forward_migration_with_state_path(self):
        """Test forward migration preserves state_path."""
        v2_data = {
            "quam": {
                "version": 2,
                "state_path": "/path/to/state",
                "raise_error_missing_reference": True
            }
        }
        
        v3_data = Migrate.forward(v2_data)
        
        expected = {
            "quam": {
                "version": 3,
                "state_path": "/path/to/state",
                "raise_error_missing_reference": True,
                "include_defaults_in_save": False  # Preserve existing behavior
            }
        }
        assert v3_data == expected

    def test_forward_migration_with_additional_sections(self):
        """Test forward migration preserves other config sections."""
        v2_data = {
            "quam": {
                "version": 2,
                "state_path": None,
                "raise_error_missing_reference": False
            },
            "other_section": {
                "some_key": "some_value"
            }
        }
        
        v3_data = Migrate.forward(v2_data)
        
        expected = {
            "quam": {
                "version": 3,
                "state_path": None,
                "raise_error_missing_reference": False,
                "include_defaults_in_save": False
            },
            "other_section": {
                "some_key": "some_value"
            }
        }
        assert v3_data == expected

    def test_backward_migration_minimal_config(self):
        """Test backward migration v3 → v2 with minimal config data."""
        v3_data = {
            "quam": {
                "version": 3,
                "state_path": None,
                "raise_error_missing_reference": False,
                "include_defaults_in_save": True
            }
        }
        
        v2_data = Migrate.backward(v3_data)
        
        expected = {
            "quam": {
                "version": 2,
                "state_path": None,
                "raise_error_missing_reference": False
                # include_defaults_in_save removed
            }
        }
        assert v2_data == expected

    def test_backward_migration_with_state_path(self):
        """Test backward migration preserves state_path."""
        v3_data = {
            "quam": {
                "version": 3,
                "state_path": "/path/to/state",
                "raise_error_missing_reference": True,
                "include_defaults_in_save": False
            }
        }
        
        v2_data = Migrate.backward(v3_data)
        
        expected = {
            "quam": {
                "version": 2,
                "state_path": "/path/to/state",
                "raise_error_missing_reference": True
                # include_defaults_in_save removed
            }
        }
        assert v2_data == expected

    def test_backward_migration_with_additional_sections(self):
        """Test backward migration preserves other config sections."""
        v3_data = {
            "quam": {
                "version": 3,
                "state_path": None,
                "raise_error_missing_reference": False,
                "include_defaults_in_save": True
            },
            "other_section": {
                "some_key": "some_value"
            }
        }
        
        v2_data = Migrate.backward(v3_data)
        
        expected = {
            "quam": {
                "version": 2,
                "state_path": None,
                "raise_error_missing_reference": False
                # include_defaults_in_save removed
            },
            "other_section": {
                "some_key": "some_value"
            }
        }
        assert v2_data == expected


class TestConfigMigrationV2V3EdgeCases:
    """Test edge cases for config migration from version 2 to version 3."""

    def test_forward_migration_preserves_existing_behavior(self):
        """Test that forward migration sets include_defaults_in_save = False to preserve v2 behavior."""
        # In v2, the default behavior was include_defaults=False (exclude defaults to save space)
        # Migration should preserve this behavior by setting include_defaults_in_save = False
        v2_data = {
            "quam": {
                "version": 2,
                "state_path": None,
                "raise_error_missing_reference": False
            }
        }
        
        v3_data = Migrate.forward(v2_data)
        
        # Should preserve existing space-saving behavior
        assert v3_data["quam"]["include_defaults_in_save"] is False

    def test_backward_migration_removes_include_defaults_field(self):
        """Test that backward migration removes include_defaults_in_save field completely."""
        v3_data = {
            "quam": {
                "version": 3,
                "state_path": None,
                "raise_error_missing_reference": False,
                "include_defaults_in_save": True  # Doesn't matter what value it had
            }
        }
        
        v2_data = Migrate.backward(v3_data)
        
        # Field should be completely removed
        assert "include_defaults_in_save" not in v2_data["quam"]
        assert v2_data["quam"]["version"] == 2

    def test_forward_migration_does_not_modify_input(self):
        """Test that forward migration doesn't modify the input data."""
        original_v2_data = {
            "quam": {
                "version": 2,
                "state_path": None,
                "raise_error_missing_reference": False
            }
        }
        
        # Create a copy to verify original isn't modified
        v2_data_copy = {
            "quam": {
                "version": 2,
                "state_path": None,
                "raise_error_missing_reference": False
            }
        }
        
        v3_data = Migrate.forward(v2_data_copy)
        
        # Original should be unchanged
        assert v2_data_copy == original_v2_data
        # Result should have the new field
        assert v3_data["quam"]["include_defaults_in_save"] is False

    def test_backward_migration_does_not_modify_input(self):
        """Test that backward migration doesn't modify the input data."""
        original_v3_data = {
            "quam": {
                "version": 3,
                "state_path": None,
                "raise_error_missing_reference": False,
                "include_defaults_in_save": True
            }
        }
        
        # Create a copy to verify original isn't modified
        v3_data_copy = {
            "quam": {
                "version": 3,
                "state_path": None,
                "raise_error_missing_reference": False,
                "include_defaults_in_save": True
            }
        }
        
        v2_data = Migrate.backward(v3_data_copy)
        
        # Original should be unchanged
        assert v3_data_copy == original_v3_data
        # Result should not have the field
        assert "include_defaults_in_save" not in v2_data["quam"]


class TestConfigMigrationV2V3RoundTrip:
    """Test round-trip migrations to ensure consistency."""

    def test_round_trip_forward_then_backward(self):
        """Test v2 → v3 → v2 round trip."""
        original_v2_data = {
            "quam": {
                "version": 2,
                "state_path": "/test/path",
                "raise_error_missing_reference": True
            },
            "other_section": {"key": "value"}
        }
        
        # Forward migration
        v3_data = Migrate.forward(original_v2_data.copy())
        assert v3_data["quam"]["version"] == 3
        assert v3_data["quam"]["include_defaults_in_save"] is False
        
        # Backward migration
        restored_v2_data = Migrate.backward(v3_data.copy())
        assert restored_v2_data == original_v2_data

    def test_round_trip_backward_then_forward(self):
        """Test v3 → v2 → v3 round trip."""
        original_v3_data = {
            "quam": {
                "version": 3,
                "state_path": "/test/path",
                "raise_error_missing_reference": True,
                "include_defaults_in_save": False
            },
            "other_section": {"key": "value"}
        }
        
        # Backward migration
        v2_data = Migrate.backward(original_v3_data.copy())
        assert v2_data["quam"]["version"] == 2
        assert "include_defaults_in_save" not in v2_data["quam"]
        
        # Forward migration
        restored_v3_data = Migrate.forward(v2_data.copy())
        
        # Should restore to same structure with include_defaults_in_save = False
        expected = {
            "quam": {
                "version": 3,
                "state_path": "/test/path",
                "raise_error_missing_reference": True,
                "include_defaults_in_save": False  # Always False from forward migration
            },
            "other_section": {"key": "value"}
        }
        assert restored_v3_data == expected