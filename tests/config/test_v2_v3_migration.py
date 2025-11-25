"""Test v2 to v3 migration for include_defaults_in_serialization field."""

import pytest
from quam.config.cli.migrations.v2_v3 import Migrate


def test_forward_migration_adds_serialization_section():
    """Test that forward migration (v2→v3) adds serialization section."""
    v2_config = {
        "quam": {
            "version": 2,
            "state_path": None,
            "raise_error_missing_reference": False,
        }
    }

    v3_config = Migrate.forward(v2_config)

    assert v3_config["quam"]["version"] == 3
    assert "serialization" in v3_config["quam"]
    assert v3_config["quam"]["serialization"]["include_defaults"] is True
    # Ensure other fields are preserved
    assert v3_config["quam"]["state_path"] is None
    assert v3_config["quam"]["raise_error_missing_reference"] is False


def test_backward_migration_removes_serialization_section():
    """Test that backward migration (v3→v2) removes serialization section."""
    v3_config = {
        "quam": {
            "version": 3,
            "state_path": None,
            "raise_error_missing_reference": False,
            "serialization": {"include_defaults": True},
        }
    }

    v2_config = Migrate.backward(v3_config)

    assert v2_config["quam"]["version"] == 2
    assert "serialization" not in v2_config["quam"]
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
    assert v3_config["quam"]["serialization"]["include_defaults"] is True


def test_migration_versions_are_correct():
    """Test that migration class has correct version numbers."""
    assert Migrate.from_version == 2
    assert Migrate.to_version == 3
