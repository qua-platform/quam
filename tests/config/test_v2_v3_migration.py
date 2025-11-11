"""Test v2 to v3 migration for include_defaults_in_serialization field."""

import pytest
from quam.config.cli.migrations.v2_v3 import Migrate


def test_forward_migration_adds_include_defaults_field():
    """Test that forward migration (v2→v3) adds include_defaults_in_serialization field."""
    v2_config = {
        "quam": {
            "version": 2,
            "state_path": None,
            "raise_error_missing_reference": False,
        }
    }

    v3_config = Migrate.forward(v2_config)

    assert v3_config["quam"]["version"] == 3
    assert "include_defaults_in_serialization" in v3_config["quam"]
    assert v3_config["quam"]["include_defaults_in_serialization"] is True
    # Ensure other fields are preserved
    assert v3_config["quam"]["state_path"] is None
    assert v3_config["quam"]["raise_error_missing_reference"] is False


def test_backward_migration_removes_include_defaults_field():
    """Test that backward migration (v3→v2) removes include_defaults_in_serialization field."""
    v3_config = {
        "quam": {
            "version": 3,
            "state_path": None,
            "raise_error_missing_reference": False,
            "include_defaults_in_serialization": True,
        }
    }

    v2_config = Migrate.backward(v3_config)

    assert v2_config["quam"]["version"] == 2
    assert "include_defaults_in_serialization" not in v2_config["quam"]
    # Ensure other fields are preserved
    assert v2_config["quam"]["state_path"] is None
    assert v2_config["quam"]["raise_error_missing_reference"] is False


def test_forward_migration_with_state_path():
    """Test forward migration preserves state_path."""
    from pathlib import Path

    v2_config = {
        "quam": {
            "version": 2,
            "state_path": "/path/to/state.json",
            "raise_error_missing_reference": True,
        }
    }

    v3_config = Migrate.forward(v2_config)

    assert v3_config["quam"]["state_path"] == "/path/to/state.json"
    assert v3_config["quam"]["raise_error_missing_reference"] is True
    assert v3_config["quam"]["include_defaults_in_serialization"] is True


def test_migration_versions_are_correct():
    """Test that migration class has correct version numbers."""
    assert Migrate.from_version == 2
    assert Migrate.to_version == 3
