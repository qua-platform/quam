"""Test to_dict() explicit parameter behavior (backward compatibility)."""

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


def test_to_dict_explicit_include_defaults_true():
    """Test that explicit include_defaults=True includes defaults."""
    comp = SimpleComponent(required_val=1)
    result = comp.to_dict(include_defaults=True)

    assert result["required_val"] == 1
    assert result["optional_val"] == 42
    assert result["optional_str"] == "default_string"
    assert result["optional_list"] == []


def test_to_dict_explicit_include_defaults_false():
    """Test that explicit include_defaults=False excludes defaults."""
    comp = SimpleComponent(required_val=1)
    result = comp.to_dict(include_defaults=False)

    assert result["required_val"] == 1
    assert "optional_val" not in result
    assert "optional_str" not in result
    assert "optional_list" not in result


def test_to_dict_default_excludes_defaults():
    """Test that to_dict() without parameters excludes defaults (backward compatibility)."""
    comp = SimpleComponent(required_val=1)
    result = comp.to_dict()

    assert result["required_val"] == 1
    assert "optional_val" not in result
    assert "optional_str" not in result
    assert "optional_list" not in result


def test_to_dict_nested_respects_include_defaults_param():
    """Test that nested components respect include_defaults parameter."""
    simple = SimpleComponent(required_val=5, optional_val=100)
    nested = NestedComponent(name="test", simple=simple)

    result = nested.to_dict(include_defaults=True)

    assert result["name"] == "test"
    assert result["count"] == 10  # default value included
    assert "simple" in result

    # Nested component should also include defaults
    simple_result = result["simple"]
    assert simple_result["required_val"] == 5
    assert simple_result["optional_val"] == 100
    assert simple_result["optional_str"] == "default_string"
    assert simple_result["optional_list"] == []


def test_to_dict_nested_excludes_defaults_by_default():
    """Test that nested components exclude defaults by default."""
    simple = SimpleComponent(required_val=5, optional_val=100)
    nested = NestedComponent(name="test", simple=simple)

    result = nested.to_dict()

    assert result["name"] == "test"
    assert "count" not in result  # default value excluded by default
    assert "simple" in result

    # Nested component should also exclude defaults
    simple_result = result["simple"]
    assert simple_result["required_val"] == 5
    assert simple_result["optional_val"] == 100
    assert "optional_str" not in simple_result
    assert "optional_list" not in simple_result
