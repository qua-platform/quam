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


@pytest.fixture
def machine():
    return BareQuamRoot(
        required_component=BasicQuamComponent(a="#/required_component_2/a"),
        required_component_2=BasicQuamComponent(a=43),
    )


def test_overwrite_reference_error(machine):
    assert machine.required_component.a == 43

    with pytest.raises(ValueError):
        machine.required_component.a = 42


def test_overwrite_reference_after_None(machine):
    assert machine.required_component.a == 43

    machine.required_component.a = None

    assert machine.required_component.a is None

    machine.required_component.a = 42

    assert machine.required_component.a == 42


def test_overwrite_reference_to_reference(machine):
    machine.required_component.a = "#/required_component_2/a"
    assert machine.required_component.a == 43

    machine.required_component.a = "#/required_component_2"
    assert machine.required_component.a == machine.required_component_2


def test_overwrite_value_to_reference(machine):
    assert machine.required_component_2.a == 43
    machine.required_component_2.a = "#/required_component_2"
    assert machine.required_component_2.a == machine.required_component_2


def test_overwrite_nonexistent_to_value(machine):
    machine.required_component.b = 43


def test_overwrite_nonexistent_to_ref(machine):
    machine.required_component.b = "#/required_component_2/a"
    assert machine.required_component.b == 43


def test_overwrite_nonexistent_to_None(machine):
    machine.required_component.b = None
    assert machine.required_component.b is None


def test_dict_overwrite_ref(machine):
    d = QuamDict(a="#./b", b=42)
    assert d._initialized
    assert d.a == 42

    with pytest.raises(ValueError):
        d.a = 43

    with pytest.raises(ValueError):
        d["a"] = 43
