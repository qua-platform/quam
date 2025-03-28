import pytest
from quam.core.operation.function_properties import FunctionProperties
from quam.core.quam_classes import quam_dataclass
from quam.components import QuantumComponent


@quam_dataclass
class DummyQuantumComponent(QuantumComponent):
    """Dummy component for testing."""

    pass


def test_function_properties_initialization():
    """Test basic initialization of FunctionProperties."""
    props = FunctionProperties(
        quantum_component_name="component",
        quantum_component_type=DummyQuantumComponent,
        name="test_function",
        required_args=["arg1", "arg2"],
        optional_args={"opt1": 1, "opt2": "default"},
    )

    assert props.quantum_component_name == "component"
    assert props.quantum_component_type == DummyQuantumComponent
    assert props.name == "test_function"
    assert props.required_args == ["arg1", "arg2"]
    assert props.optional_args == {"opt1": 1, "opt2": "default"}


def test_from_function_with_valid_function():
    """Test from_function with a valid function signature."""

    def valid_operation(
        component: DummyQuantumComponent, arg1: int, arg2: str, opt1: int = 1
    ):
        pass

    props = FunctionProperties.from_function(valid_operation)

    assert props.quantum_component_name == "component"
    assert props.quantum_component_type == DummyQuantumComponent
    assert props.name == "valid_operation"
    assert props.required_args == ["arg1", "arg2"]
    assert props.optional_args == {"opt1": 1}


def test_from_function_with_only_required_args():
    """Test from_function with a function that has only required arguments."""

    def operation(component: DummyQuantumComponent, arg1: int, arg2: str):
        pass

    props = FunctionProperties.from_function(operation)

    assert props.quantum_component_name == "component"
    assert props.required_args == ["arg1", "arg2"]
    assert props.optional_args == {}


def test_from_function_with_only_optional_args():
    """Test from_function with a function that has only optional arguments."""

    def operation(
        component: DummyQuantumComponent, arg1: int = 1, arg2: str = "default"
    ):
        pass

    props = FunctionProperties.from_function(operation)

    assert props.quantum_component_name == "component"
    assert props.required_args == []
    assert props.optional_args == {"arg1": 1, "arg2": "default"}


def test_from_function_with_no_args():
    """Test from_function with a function that has only the component parameter."""

    def operation(component: DummyQuantumComponent):
        pass

    props = FunctionProperties.from_function(operation)

    assert props.quantum_component_name == "component"
    assert props.required_args == []
    assert props.optional_args == {}


def test_from_function_invalid_first_arg():
    """Test from_function with a function that doesn't have QuantumComponent as
    first arg."""

    def invalid_operation(x: int, component: DummyQuantumComponent):
        pass

    with pytest.raises(
        ValueError, match="must accept a QuantumComponent as its first argument"
    ):
        FunctionProperties.from_function(invalid_operation)


def test_from_function_no_args():
    """Test from_function with a function that has no arguments."""

    def invalid_operation():
        pass

    with pytest.raises(ValueError, match="must accept at least one argument"):
        FunctionProperties.from_function(invalid_operation)


def test_from_function_wrong_type():
    """Test from_function with a function that has wrong type for first argument."""

    def invalid_operation(component: int):
        pass

    with pytest.raises(
        ValueError, match="must accept a QuantumComponent as its first argument"
    ):
        FunctionProperties.from_function(invalid_operation)


def test_from_function_with_optional_type():
    """Test handling of Optional type hints."""
    from typing import Optional

    def operation(component: DummyQuantumComponent, arg: Optional[int] = None):
        pass

    props = FunctionProperties.from_function(operation)
    assert props.optional_args["arg"] is None


def test_function_properties_container_independence():
    """Test that container attributes are independent between instances."""
    props1 = FunctionProperties(
        quantum_component_name="comp1",
        quantum_component_type=DummyQuantumComponent,
        required_args=["arg1"],
        optional_args={"opt1": 1},
    )
    props2 = FunctionProperties(
        quantum_component_name="comp2",
        quantum_component_type=DummyQuantumComponent,
        required_args=["arg1"],
        optional_args={"opt1": 1},
    )

    # Modify containers in first instance
    props1.required_args.append("arg2")
    props1.optional_args["opt2"] = 2

    # Check that second instance wasn't affected
    assert props2.required_args == ["arg1"]
    assert props2.optional_args == {"opt1": 1}


def test_function_properties_invalid_argument_name():
    """Test that invalid argument names are rejected."""
    with pytest.raises(ValueError, match="Invalid argument name: '123invalid'"):
        FunctionProperties(
            quantum_component_name="comp",
            quantum_component_type=DummyQuantumComponent,
            required_args=["123invalid"],
        )

    with pytest.raises(ValueError, match="Invalid argument name: 'invalid@name'"):
        FunctionProperties(
            quantum_component_name="comp",
            quantum_component_type=DummyQuantumComponent,
            optional_args={"invalid@name": 1},
        )


def test_function_properties_python_keyword_argument():
    """Test that Python keywords are rejected as argument names."""
    with pytest.raises(
        ValueError, match="Argument name cannot be a Python keyword: 'class'"
    ):
        FunctionProperties(
            quantum_component_name="comp",
            quantum_component_type=DummyQuantumComponent,
            required_args=["class"],
        )

    with pytest.raises(
        ValueError, match="Argument name cannot be a Python keyword: 'return'"
    ):
        FunctionProperties(
            quantum_component_name="comp",
            quantum_component_type=DummyQuantumComponent,
            optional_args={"return": 1},
        )


def test_from_function_with_complex_type_hints():
    """Test handling of complex type hints like Union and Optional."""
    from typing import Union, Optional

    def operation(
        component: DummyQuantumComponent,
        arg1: Union[int, str],
        arg2: Optional[float] = None,
    ):
        pass

    props = FunctionProperties.from_function(operation)
    assert props.required_args == ["arg1"]
    assert props.optional_args == {"arg2": None}


def test_from_function_without_annotations():
    """Test that function works with parameters that have no type annotations."""

    def operation(component, arg1, arg2=None):
        pass

    with pytest.raises(ValueError, match="missing type annotation"):
        FunctionProperties.from_function(operation)


def test_from_function_with_return_type():
    """Test that return type is correctly captured."""

    def operation(component: DummyQuantumComponent) -> int:
        return 42

    props = FunctionProperties.from_function(operation)
    assert props.return_type == int


def test_from_function_with_optional_return_type():
    """Test handling of Optional return type."""
    from typing import Optional

    def operation(component: DummyQuantumComponent) -> Optional[int]:
        return None

    props = FunctionProperties.from_function(operation)
    assert props.return_type == Optional[int]


def test_from_function_with_qua_return_type():
    """Test handling of QUA variable return types."""
    from quam.utils.qua_types import QuaVariableBool

    def operation(component: DummyQuantumComponent) -> QuaVariableBool:
        pass

    props = FunctionProperties.from_function(operation)
    assert props.return_type == QuaVariableBool


def test_from_function_without_return_type():
    """Test handling of functions without return type annotation."""

    def operation(component: DummyQuantumComponent):
        pass

    props = FunctionProperties.from_function(operation)
    assert props.return_type is None
