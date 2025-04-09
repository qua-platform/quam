from quam import QuamRoot, QuamComponent, quam_dataclass
import warnings


@quam_dataclass
class Component(QuamComponent):
    y: int = 2


@quam_dataclass
class Root(QuamRoot):
    a: Component
    b: Component = "#/a"


def test_quam_root_reference():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        root = Root(a=Component())
        assert root.a is root.b


def test_quam_root_reference_to_dict():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        root = Root(a="#/b", b=Component())
        d = root.to_dict()
        assert d == {
            "a": "#/b",
            "b": {"__class__": "test_quam_root_referencing.Component"},
            "__class__": "test_quam_root_referencing.Root",
        }
