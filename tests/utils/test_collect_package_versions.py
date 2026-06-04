from unittest.mock import patch

import pytest

from quam.utils.general import collect_package_versions


def test_empty_dict():
    assert collect_package_versions({}) == {}


def test_single_class():
    contents = {"__class__": "quam.core.QuamRoot"}
    versions = collect_package_versions(contents)
    assert "quam" in versions
    assert isinstance(versions["quam"], str)


def test_deduplicates_same_package():
    contents = {
        "__class__": "quam.core.QuamRoot",
        "child": {"__class__": "quam.components.channels.IQChannel"},
    }
    versions = collect_package_versions(contents)
    assert list(versions.keys()).count("quam") == 1


def test_multiple_packages():
    contents = {
        "__class__": "quam.core.QuamRoot",
        "child": {"__class__": "other_pkg.components.MyComponent"},
    }
    with patch("importlib.metadata.version", side_effect=lambda p: {"quam": "1.0", "other_pkg": "2.0"}[p]):
        versions = collect_package_versions(contents)
    assert versions == {"other_pkg": "2.0", "quam": "1.0"}


def test_nested_list():
    contents = {
        "__class__": "quam.core.QuamRoot",
        "items": [
            {"__class__": "quam.components.pulses.SquarePulse"},
            {"__class__": "quam.components.pulses.GaussianPulse"},
        ],
    }
    versions = collect_package_versions(contents)
    assert list(versions.keys()) == ["quam"]


def test_unknown_package_omitted():
    contents = {"__class__": "nonexistent_package.SomeClass"}
    versions = collect_package_versions(contents)
    assert "nonexistent_package" not in versions


def test_main_module_omitted():
    contents = {"__class__": "MyLocalClass"}
    versions = collect_package_versions(contents)
    assert versions == {}


def test_no_class_fields():
    contents = {"value": 42, "name": "test", "nested": {"x": 1}}
    assert collect_package_versions(contents) == {}
