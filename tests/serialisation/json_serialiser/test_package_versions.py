import json
import dataclasses
from typing import Optional
from unittest.mock import patch

import pytest

from quam.core import QuamRoot, QuamComponent, quam_dataclass
from quam.core.quam_instantiation import instantiate_quam_class
from quam.serialisation.json import JSONSerialiser


@quam_dataclass
class SimpleComponent(QuamComponent):
    value: int = 0


@quam_dataclass
class SimpleRoot(QuamRoot):
    component: Optional[SimpleComponent] = None


# --- save: __package_versions__ is written ---


def test_save_includes_package_versions(tmp_path):
    root = SimpleRoot(component=SimpleComponent(value=5))
    path = tmp_path / "state.json"
    with patch("quam.serialisation.json.collect_package_versions", return_value={"quam": "1.0.0"}):
        root.save(path)

    with path.open() as f:
        data = json.load(f)

    assert "__package_versions__" in data
    assert data["__package_versions__"] == {"quam": "1.0.0"}


def test_package_versions_at_top_level_only(tmp_path):
    root = SimpleRoot(component=SimpleComponent(value=5))
    path = tmp_path / "state.json"
    with patch("quam.serialisation.json.collect_package_versions", return_value={"quam": "1.0.0"}):
        root.save(path)

    with path.open() as f:
        data = json.load(f)

    assert "__package_versions__" not in data.get("component", {})


def test_package_versions_empty_dict_not_written(tmp_path):
    root = SimpleRoot(component=SimpleComponent(value=5))
    path = tmp_path / "state.json"
    with patch("quam.serialisation.json.collect_package_versions", return_value={}):
        root.save(path)

    with path.open() as f:
        data = json.load(f)

    assert "__package_versions__" not in data


def test_package_versions_multiple_packages_written(tmp_path):
    root = SimpleRoot(component=SimpleComponent(value=5))
    path = tmp_path / "state.json"
    fake_versions = {"quam": "1.0.0", "my_lib": "2.3.4"}
    with patch("quam.serialisation.json.collect_package_versions", return_value=fake_versions):
        root.save(path)

    with path.open() as f:
        data = json.load(f)

    assert data["__package_versions__"] == fake_versions


# --- load: __package_versions__ is silently ignored ---


def test_load_ignores_package_versions():
    contents = {
        "__class__": f"{SimpleRoot.__module__}.SimpleRoot",
        "__package_versions__": {"quam": "0.5.0"},
        "component": {
            "__class__": f"{SimpleComponent.__module__}.SimpleComponent",
            "value": 7,
        },
    }
    root = instantiate_quam_class(SimpleRoot, contents)
    assert root.component.value == 7


def test_load_without_package_versions_unchanged():
    contents = {
        "__class__": f"{SimpleRoot.__module__}.SimpleRoot",
        "component": {
            "__class__": f"{SimpleComponent.__module__}.SimpleComponent",
            "value": 3,
        },
    }
    root = instantiate_quam_class(SimpleRoot, contents)
    assert root.component.value == 3


def test_roundtrip_save_load(tmp_path):
    original = SimpleRoot(component=SimpleComponent(value=42))
    path = tmp_path / "state.json"
    original.save(path)
    loaded = SimpleRoot.load(path)
    assert loaded.component.value == 42
