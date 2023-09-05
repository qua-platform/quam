from dataclasses import dataclass, field
import json

from quam_components.core.quam_classes import *
from quam_components.serialisation.json import JSONSerialiser


@dataclass
class TestQuamComponent(QuamComponent):
    int_val: int
    inner_quam: QuamComponent = None


@dataclass
class TestQuam(QuamRoot):
    int_val: int
    inner_quam: QuamComponent


def test_load_explicit_class(tmp_path):
    test_quam = TestQuamComponent(int_val=42, inner_quam=TestQuamComponent(43))

    json_serialiser = JSONSerialiser()
    json_file = tmp_path / "quam.json"

    json_serialiser.save(test_quam, path=json_file)

    with open(json_file) as f:
        contents = json.load(f)
        assert contents == {
            "int_val": 42,
            "inner_quam": {"__class__": "test_load.TestQuamComponent", "int_val": 43},
        }


def test_load_explicit_class_root(tmp_path):
    test_quam = TestQuam(int_val=42, inner_quam=TestQuamComponent(43))

    json_serialiser = JSONSerialiser()
    json_file = tmp_path / "quam.json"

    json_serialiser.save(test_quam, path=json_file)

    with open(json_file) as f:
        contents = json.load(f)
        assert contents == {
            "int_val": 42,
            "inner_quam": {"__class__": "test_load.TestQuamComponent", "int_val": 43},
            "__class__": "test_load.TestQuam",
        }
