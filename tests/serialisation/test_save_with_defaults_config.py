"""Test serialization respects include_defaults_in_serialization config."""

import json
import tempfile
from pathlib import Path
from dataclasses import field
from typing import List

import pytest
from quam.core.quam_classes import QuamComponent, QuamRoot, quam_dataclass
from quam.config.models.quam import QuamConfig
from quam.config.resolvers import get_quam_config
from unittest.mock import patch, MagicMock


@quam_dataclass
class SimpleComponent(QuamComponent):
    required_val: int
    optional_val: int = 42
    optional_str: str = "default_string"
    optional_list: List[int] = field(default_factory=list)


@quam_dataclass
class NestedComponent(QuamComponent):
    name: str
    simple: SimpleComponent
    count: int = 10


@quam_dataclass
class TestRoot(QuamRoot):
    component: SimpleComponent


def test_quamroot_save_includes_defaults_by_config():
    """Test that QuamRoot.save() includes defaults when config is True."""
    root = TestRoot(component=SimpleComponent(required_val=1))

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "state.json"
        root.save(save_path)

        with open(save_path) as f:
            saved_data = json.load(f)

        # With default config (include_defaults=True), all fields should be present
        assert "component" in saved_data
        component_data = saved_data["component"]
        assert component_data["required_val"] == 1
        assert component_data["optional_val"] == 42
        assert component_data["optional_str"] == "default_string"
        assert component_data["optional_list"] == []


def test_quamroot_save_excludes_defaults_when_config_false():
    """Test that QuamRoot.save() excludes defaults when config is False."""
    root = TestRoot(component=SimpleComponent(required_val=1))

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "state.json"

        # Mock the config to return False for include_defaults_in_serialization
        with patch("quam.serialisation.json.get_quam_config") as mock_config:
            mock_instance = MagicMock()
            mock_instance.include_defaults_in_serialization = False
            mock_config.return_value = mock_instance

            root.save(save_path)

        with open(save_path) as f:
            saved_data = json.load(f)

        # With include_defaults=False, only non-default values should be present
        component_data = saved_data["component"]
        assert component_data["required_val"] == 1
        # Default values should NOT be in the output
        assert "optional_val" not in component_data or component_data["optional_val"] != 42
        assert "optional_str" not in component_data or component_data["optional_str"] != "default_string"
        assert "optional_list" not in component_data or component_data["optional_list"] == []


def test_quamroot_save_with_nested_components_includes_all_defaults():
    """Test that nested components also include defaults when config is True."""
    simple = SimpleComponent(required_val=5, optional_val=100)
    nested = NestedComponent(name="test", simple=simple)

    @quam_dataclass
    class RootWithNested(QuamRoot):
        nested: NestedComponent

    root = RootWithNested(nested=nested)

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "state.json"
        root.save(save_path)

        with open(save_path) as f:
            saved_data = json.load(f)

        nested_data = saved_data["nested"]
        # Nested component should include its defaults
        assert nested_data["count"] == 10  # default value
        assert "name" in nested_data
        assert "simple" in nested_data

        # Deeply nested component should also include defaults
        simple_data = nested_data["simple"]
        assert simple_data["required_val"] == 5
        assert simple_data["optional_val"] == 100
        assert simple_data["optional_str"] == "default_string"
        assert simple_data["optional_list"] == []


def test_quamroot_load_old_state_without_defaults():
    """Test that loading old states (without all defaults) works correctly."""
    # Simulate an old saved state that only contains non-default values
    old_state = {
        "component": {
            "required_val": 1,
            "__class__": "test_save_with_defaults_config.SimpleComponent",
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "state.json"
        with open(save_path, "w") as f:
            json.dump(old_state, f)

        # Should be able to load without errors
        loaded = TestRoot.load(save_path)

        # Non-provided values should use defaults
        assert loaded.component.required_val == 1
        assert loaded.component.optional_val == 42
        assert loaded.component.optional_str == "default_string"
        assert loaded.component.optional_list == []


def test_quamroot_load_new_state_with_all_defaults():
    """Test that loading new states (with all defaults included) works correctly."""
    new_state = {
        "component": {
            "required_val": 1,
            "optional_val": 42,
            "optional_str": "default_string",
            "optional_list": [],
            "__class__": "test_save_with_defaults_config.SimpleComponent",
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "state.json"
        with open(save_path, "w") as f:
            json.dump(new_state, f)

        # Should be able to load without errors
        loaded = TestRoot.load(save_path)

        # All values should match the loaded state
        assert loaded.component.required_val == 1
        assert loaded.component.optional_val == 42
        assert loaded.component.optional_str == "default_string"
        assert loaded.component.optional_list == []
