from dataclasses import dataclass, field
from quam_components.core import *
from quam_components.core.quam_instantiation import *


@dataclass
class TestQuamComponent(QuamComponent):
    str_val: str


def test_instantiate_from_class():
    quam_component = TestQuamComponent("hi")
    instantiate_quam_class(quam_component)
