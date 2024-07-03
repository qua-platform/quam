import json
from typing import Dict
import pytest

from quam.serialisation import JSONSerialiser
from quam.core import QuamRoot, QuamComponent, quam_dataclass


@quam_dataclass
class QuAM(QuamRoot):
    a: int
    b: list
    c: int = None


def test_serialise_random_object(tmp_path):
    quam_root = QuAM(a=1, b=[1, 2, 3])

    serialiser = JSONSerialiser()
    path = tmp_path / "quam_root.json"
    serialiser.save(quam_root, path)

    d = json.loads(path.read_text())

    assert d == {
        "a": 1,
        "b": [1, 2, 3],
        "__class__": "test_json_serialisation.QuAM",
    }

    class RandomObject: ...

    quam_root.b = RandomObject()

    with pytest.raises(TypeError):
        serialiser.save(quam_root, path)


def test_serialise_ignore(tmp_path):
    quam_root = QuAM(a=1, b=[1, 2, 3])

    serialiser = JSONSerialiser()
    path = tmp_path / "quam_root.json"
    serialiser.save(quam_root, path, ignore=["b"])

    d = json.loads(path.read_text())

    assert d == {
        "a": 1,
        "__class__": "test_json_serialisation.QuAM",
    }


def test_serialise_ignore_nonexisting(tmp_path):
    quam_root = QuAM(a=1, b=[1, 2, 3])

    serialiser = JSONSerialiser()
    path = tmp_path / "quam_root.json"
    serialiser.save(quam_root, path, ignore=["c"])

    d = json.loads(path.read_text())

    assert d == {
        "a": 1,
        "b": [1, 2, 3],
        "__class__": "test_json_serialisation.QuAM",
    }


@quam_dataclass
class Component(QuamComponent):
    a: int


def test_component_mamping(tmp_path):
    quam_root = QuAM(a=1, b=Component(a=3), c=Component(a=4))

    serialiser = JSONSerialiser()
    path = tmp_path / "quam_root.json"
    serialiser.save(quam_root, path, content_mapping={"b.json": ["b"]})

    d = json.loads((tmp_path / "b.json").read_text())
    assert d == {
        "b": {
            "__class__": "test_json_serialisation.Component",
            "a": 3,
        }
    }


def test_component_mamping_ignore(tmp_path):
    assert not (tmp_path / "b.json").exists()

    quam_root = QuAM(a=1, b=Component(a=3), c=Component(a=4))

    serialiser = JSONSerialiser()
    path = tmp_path / "quam_root.json"
    serialiser.save(quam_root, path, ignore=["b"], content_mapping={"b.json": ["b"]})
    assert not (tmp_path / "b.json").exists()

    serialiser.save(
        quam_root, path, ignore=["b"], content_mapping={"b.json": ["b", "c"]}
    )
    d = json.loads((tmp_path / "b.json").read_text())
    assert d == {
        "c": {
            "__class__": "test_json_serialisation.Component",
            "a": 4,
        }
    }


@quam_dataclass
class QuAMWithIntDict(QuamRoot):
    a: int
    d: Dict[int, str]


def test_serialise_int_dict_keys(tmp_path):
    quam_root = QuAMWithIntDict(a=1, d={1: "a", 2: "b"})

    serialiser = JSONSerialiser()
    path = tmp_path / "quam_root.json"
    serialiser.save(quam_root, path)

    d, _ = serialiser.load(path)

    assert d == {
        "a": 1,
        "d": {
            1: "a",
            2: "b",
        },
        "__class__": "test_json_serialisation.QuAMWithIntDict",
    }
