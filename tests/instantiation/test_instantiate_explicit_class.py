from dataclasses import dataclass
from quam.core import *
from quam.core.quam_instantiation import *
from quam.utils import get_full_class_path


@dataclass
class QuamComponentTest(QuamComponent):
    str_val: str


def test_instantiate_from_class():
    quam_component = QuamComponentTest("hi")
    loaded_component = instantiate_quam_class(
        QuamComponentTest, quam_component.to_dict()
    )

    assert isinstance(loaded_component, QuamComponentTest)
    assert loaded_component.to_dict() == quam_component.to_dict()

    d = quam_component.to_dict()
    d["__class__"] = get_full_class_path(QuamComponentTest)
    loaded_explicit_component = instantiate_quam_class(QuamComponent, d)
    loaded_explicit_component2 = instantiate_quam_class(QuamComponent, d)
    assert type(loaded_explicit_component) == type(loaded_explicit_component2)

    assert isinstance(loaded_explicit_component, QuamComponentTest)
