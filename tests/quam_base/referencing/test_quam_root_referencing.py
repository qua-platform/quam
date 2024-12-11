from quam import QuamRoot, QuamComponent, quam_dataclass
import pytest


@quam_dataclass
class Component(QuamComponent):
    y: int = 2


@quam_dataclass
class Root(QuamRoot):
    a: Component
    b: Component = "#/a"


def test_quam_root_reference():
    with pytest.warns(None) as record:
        root = Root(a=Component())
        assert root.a is root.b

    # Ensure no warnings were raised
    assert len(record) == 0


def test_quam_root_reference_to_dict():
    with pytest.warns(None) as record:
        root = Root(a="#/b", b=Component())
        d = root.to_dict()
        assert d == {
            "a": "#/b",
            "b": {},
            "__class__": "test_quam_root_referencing.Root",
        }

    # Ensure no warnings were raised
    assert len(record) == 0
