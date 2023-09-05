from dataclasses import dataclass, field
from quam_components.core import *
from quam_components.core.quam_instantiation import *


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
    d['__class__'] = "quam_components.tests.test_instantiate_explicit_class.TestQuamComponent"
    loaded_explicit_component = instantiate_quam_class(
        QuamComponent, d)
    
    assert isinstance(loaded_explicit_component, TestQuamComponent)