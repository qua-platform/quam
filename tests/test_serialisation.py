import json
from dataclasses import dataclass

from quam_components.serialisation.json_serialiser import JSONSerialiser
from quam_components.core.quam_base import QuamBase, QuamComponent


def test_serialise_empty_quam_base(tmp_path):
    quam = QuamBase()
    json_serialiser = JSONSerialiser()

    file = tmp_path / "quam2.json"

    json_serialiser.save(quam, path=file)

    with open(file) as f:
        contents = json.load(f)
        assert contents == {}

    contents = json_serialiser.load(file)
    assert contents["contents"] == {}
    assert contents["component_mapping"] == {}
    assert contents["default_filename"] == "quam2.json"
    assert contents["default_foldername"] == None


def test_content_mapping(tmp_path):
    @dataclass(kw_only=True, eq=False)
    class QuamBase1(QuamBase):
        int_val: int
        quam_component: QuamComponent
        quam_component_separate: QuamComponent

    @dataclass(kw_only=True, eq=False)
    class QuamComponent1(QuamComponent):
        int_val: int

    quam = QuamBase1(
        int_val=1,
        quam_component=QuamComponent1(int_val=2),
        quam_component_separate=QuamComponent1(int_val=3),
    )

    json_serialiser = JSONSerialiser()
    json_file = tmp_path / "quam"

    json_serialiser.save(quam, path=json_file)
    contents, metadata = json_serialiser.load(json_file)
    assert list(contents.keys()) == ["int_val", "quam_component", "quam_component_separate"]

    