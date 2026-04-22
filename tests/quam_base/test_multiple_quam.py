from typing import Optional
import warnings
import pytest
from quam.core.quam_classes import QuamComponent, QuamRoot, quam_dataclass


@quam_dataclass
class QuamComponentTest(QuamComponent):
    a: int
    b: int


@quam_dataclass
class QuamComponentNestedTest(QuamComponentTest):
    component: Optional[QuamComponentTest] = None


@quam_dataclass
class QuamRootTest(QuamRoot):
    component: Optional[QuamComponentTest] = None


def test_get_root():
    component = QuamComponentTest(a=1, b=2)
    assert component.get_root() is None

    machine = QuamRootTest(component=component)
    assert machine.component.a == 1
    assert machine.component.b == 2
    assert machine.component.get_root() == machine


def test_get_root_nested():
    nested_component = QuamComponentTest(a=1, b=2)
    component = QuamComponentNestedTest(a=1, b=2, component=nested_component)

    assert nested_component.get_root() is None
    assert component.get_root() is None

    machine = QuamRootTest(component=component)
    assert machine.component.get_root() == machine
    assert machine.component.component.get_root() == machine


def test_multiple_quam():
    component = QuamComponentTest(a=1, b=2)
    machine = QuamRootTest(component=component)

    component2 = QuamComponentTest(a=3, b=4)
    machine2 = QuamRootTest(component=component2)

    assert component.get_root() == machine
    assert component2.get_root() == machine2

    assert machine.get_root() == machine
    assert machine2.get_root() == machine2


def test_multiple_quam_nested():
    nested_component = QuamComponentTest(a=1, b=2)
    component = QuamComponentNestedTest(a=1, b=2, component=nested_component)

    component2 = QuamComponentTest(a=3, b=4)

    assert nested_component.get_root() is None
    assert component.get_root() is None
    assert component2.get_root() is None

    machine = QuamRootTest(component=component)
    machine2 = QuamRootTest(component=component2)

    assert machine.component.get_root() == machine
    assert machine.component.component.get_root() == machine
    assert machine2.component.get_root() == machine2
    assert machine2.component.get_root() == machine2


def test_multiple_quam_reference():
    component = QuamComponentTest(a=1, b="#/component/a")
    machine = QuamRootTest(component=component)

    component2 = QuamComponentTest(a=3, b="#/component/a")
    machine2 = QuamRootTest(component=component2)

    assert component.b == 1
    assert component2.b == 3


def test_detached_root():
    component = QuamComponentTest(a=1, b=2)

    with pytest.warns(UserWarning, match="No QuamRoot initialized, cannot retrieve"):
        assert component._get_referenced_value("#/component/a") == "#/component/a"

    machine = QuamRootTest(component=QuamComponentTest(a=4, b=5))

    with pytest.warns(
        UserWarning,
        match=("This component is not part of any QuamRoot, using last"),
    ):
        assert component._get_referenced_value("#/component/a") == 4

    component2 = QuamComponentTest(a=3, b="#/component/a")
    QuamRootTest(component=component2)

    with pytest.warns(
        UserWarning,
        match=("This component is not part of any QuamRoot, using last"),
    ):
        assert component._get_referenced_value("#/component/a") == 3

    machine.component = component
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert component._get_referenced_value("#/component/a") == 1
