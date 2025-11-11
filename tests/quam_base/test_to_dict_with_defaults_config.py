"""Test to_dict() behavior with include_defaults_in_serialization config."""

from dataclasses import field
from typing import List

import pytest
from quam.core.quam_classes import QuamComponent, quam_dataclass
from quam.config.models.quam import QuamConfig
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


def test_to_dict_explicit_include_defaults_true_overrides_config():
    """Test that explicit include_defaults=True parameter overrides config."""
    comp = SimpleComponent(required_val=1)

    # Even if config says False, explicit True should include defaults
    with patch("quam.core.quam_classes.get_quam_config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.include_defaults_in_serialization = False
        mock_config.return_value = mock_instance

        result = comp.to_dict(include_defaults=True)

    assert result["required_val"] == 1
    assert result["optional_val"] == 42
    assert result["optional_str"] == "default_string"
    assert result["optional_list"] == []


def test_to_dict_explicit_include_defaults_false_overrides_config():
    """Test that explicit include_defaults=False parameter overrides config."""
    comp = SimpleComponent(required_val=1)

    # Even if config says True, explicit False should exclude defaults
    with patch("quam.core.quam_classes.get_quam_config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.include_defaults_in_serialization = True
        mock_config.return_value = mock_instance

        result = comp.to_dict(include_defaults=False)

    assert result["required_val"] == 1
    assert "optional_val" not in result
    assert "optional_str" not in result
    assert "optional_list" not in result


def test_to_dict_uses_config_when_include_defaults_not_specified():
    """Test that to_dict() uses config setting when include_defaults not specified."""
    comp = SimpleComponent(required_val=1)

    # Config says True, no explicit parameter → should include defaults
    with patch("quam.core.quam_classes.get_quam_config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.include_defaults_in_serialization = True
        mock_config.return_value = mock_instance

        result = comp.to_dict()

    assert result["required_val"] == 1
    assert result["optional_val"] == 42
    assert result["optional_str"] == "default_string"
    assert result["optional_list"] == []


def test_to_dict_uses_config_false_when_not_specified():
    """Test that to_dict() respects config=False when include_defaults not specified."""
    comp = SimpleComponent(required_val=1)

    # Config says False, no explicit parameter → should exclude defaults
    with patch("quam.core.quam_classes.get_quam_config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.include_defaults_in_serialization = False
        mock_config.return_value = mock_instance

        result = comp.to_dict()

    assert result["required_val"] == 1
    assert "optional_val" not in result
    assert "optional_str" not in result
    assert "optional_list" not in result


def test_to_dict_nested_respects_config():
    """Test that nested components also respect the config setting."""
    simple = SimpleComponent(required_val=5, optional_val=100)
    nested = NestedComponent(name="test", simple=simple)

    with patch("quam.core.quam_classes.get_quam_config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.include_defaults_in_serialization = True
        mock_config.return_value = mock_instance

        result = nested.to_dict()

    assert result["name"] == "test"
    assert result["count"] == 10  # default value included
    assert "simple" in result

    # Nested component should also include defaults
    simple_result = result["simple"]
    assert simple_result["required_val"] == 5
    assert simple_result["optional_val"] == 100
    assert simple_result["optional_str"] == "default_string"
    assert simple_result["optional_list"] == []


def test_to_dict_nested_excludes_defaults_when_config_false():
    """Test that nested components exclude defaults when config is False."""
    simple = SimpleComponent(required_val=5, optional_val=100)
    nested = NestedComponent(name="test", simple=simple)

    with patch("quam.core.quam_classes.get_quam_config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.include_defaults_in_serialization = False
        mock_config.return_value = mock_instance

        result = nested.to_dict()

    assert result["name"] == "test"
    assert "count" not in result  # default value excluded
    assert "simple" in result

    # Nested component should also exclude defaults
    simple_result = result["simple"]
    assert simple_result["required_val"] == 5
    assert simple_result["optional_val"] == 100
    assert "optional_str" not in simple_result
    assert "optional_list" not in simple_result


def test_to_dict_explicit_parameter_overrides_for_nested():
    """Test that explicit include_defaults parameter overrides config for nested components."""
    simple = SimpleComponent(required_val=5)
    nested = NestedComponent(name="test", simple=simple)

    # Config says False, but explicit True should include defaults
    with patch("quam.core.quam_classes.get_quam_config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.include_defaults_in_serialization = False
        mock_config.return_value = mock_instance

        result = nested.to_dict(include_defaults=True)

    assert result["count"] == 10  # default included despite config=False
    simple_result = result["simple"]
    assert simple_result["optional_val"] == 42
    assert simple_result["optional_str"] == "default_string"
