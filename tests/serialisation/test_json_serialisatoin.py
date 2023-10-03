from dataclasses import dataclass
import json

import pytest

from quam_components.serialisation import JSONSerialiser
from quam_components.core import QuamRoot, QuamComponent


@dataclass
class QuAM(QuamRoot):
    a: int
    b: list


def test_serialise_random_object(tmp_path):
    quam_root = QuAM(a=1, b=[1, 2, 3])

    serialiser = JSONSerialiser()
    path = tmp_path / "quam_root.json"
    serialiser.save(quam_root, path)

    d = json.loads(path.read_text())

    assert d == {
        "a": 1,
        "b": [1, 2, 3],
        "__class__": "test_json_serialisatoin.QuAM",
    }

    class RandomObject:
        ...

    quam_root.b = RandomObject()

    with pytest.raises(TypeError):
        serialiser.save(quam_root, path)
