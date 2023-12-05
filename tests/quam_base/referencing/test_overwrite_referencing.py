import pytest

from quam.core import *


@quam_dataclass
class BasicQuamComponent(QuamComponent):
    a: int = 4


@quam_dataclass
class BareQuamRoot(QuamRoot):
    required_component: BasicQuamComponent
    required_component_2: BasicQuamComponent
    optional_component: BasicQuamComponent = None


def test_overwrite_reference_error():
    machine = BareQuamRoot(
        required_component=BasicQuamComponent(a="#/required_component_2/a"),
        required_component_2=BasicQuamComponent(a=43),
    )

    assert machine.required_component.a == 43

    with pytest.raises(ValueError):
        machine.required_component.a = 42


def test_overwrite_reference_after_None():
    machine = BareQuamRoot(
        required_component=BasicQuamComponent(a="#/required_component_2/a"),
        required_component_2=BasicQuamComponent(a=43),
    )

    assert machine.required_component.a == 43

    machine.required_component.a = None

    assert machine.required_component.a is None

    machine.required_component.a = 42

    assert machine.required_component.a == 42
