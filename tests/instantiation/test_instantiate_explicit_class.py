from dataclasses import dataclass
from typing import List, Union
from quam.core import *
from quam.core.quam_instantiation import *
from quam.utils import get_full_class_path


@quam_dataclass
class QuamComponentTest(QuamComponent):
    str_val: str


def test_instantiate_from_class():
    quam_component = QuamComponentTest(str_val="hi")
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


def test_instantiate_nondefault_list_from_dict():
    @quam_dataclass
    class QuamBasicComponent(QuamComponent):
        l: Union[int, List[int]] = 42

    quam_component = QuamBasicComponent(l=[1, 2, 3])

    d = quam_component.to_dict()
    instantiate_quam_class(QuamBasicComponent, d)
