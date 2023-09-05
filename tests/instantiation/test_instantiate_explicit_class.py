from dataclasses import dataclass
from quam_components.core import *
from quam_components.core.quam_instantiation import *
from quam_components.core.utils import get_full_class_path


@dataclass
class TestQuamComponent(QuamComponent):
    str_val: str


def test_instantiate_from_class():
    quam_component = TestQuamComponent("hi")
    loaded_component = instantiate_quam_class(
        TestQuamComponent, quam_component.to_dict()
    )

    assert isinstance(loaded_component, TestQuamComponent)
    assert loaded_component.to_dict() == quam_component.to_dict()

    d = quam_component.to_dict()
    d["__class__"] = get_full_class_path(TestQuamComponent)
    loaded_explicit_component = instantiate_quam_class(QuamComponent, d)
    loaded_explicit_component2 = instantiate_quam_class(QuamComponent, d)
    assert type(loaded_explicit_component) == type(loaded_explicit_component2)

    assert isinstance(loaded_explicit_component, TestQuamComponent)
