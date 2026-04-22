import pytest
from quam.core.operation.operation import Operation
from quam.core.operation.function_properties import FunctionProperties
from quam.components import Qubit
from quam.components.macro import QubitMacro
from quam.core import quam_dataclass


def test_operation_initialization():
    def sample_op(qubit: Qubit):
        pass

    op = Operation(sample_op)
    assert op.func == sample_op
    assert isinstance(op.properties, FunctionProperties)
    assert op.properties.name == "sample_op"
    assert op.properties.quantum_component_type == Qubit


def test_operation_get_macro(test_qubit):
    def x_gate(qubit: Qubit):
        pass

    op = Operation(x_gate)
    retrieved_macro = op.get_macro(test_qubit)
    assert retrieved_macro == test_qubit.macros["x_gate"]


def test_operation_get_macro_missing(test_qubit):
    def missing_op(qubit: Qubit):
        pass

    op = Operation(missing_op)
    with pytest.raises(KeyError, match="Operation 'missing_op' is not implemented"):
        op.get_macro(test_qubit)


def test_operation_call(test_qubit):
    def test_op(qubit: Qubit, amplitude: float = 1.0):
        pass

    op = Operation(test_op)
    result = op(test_qubit, amplitude=0.5)

    # Check results
    assert result[0] == test_qubit  # First element should be the qubit
    assert result[1] == ()  # No positional args
    assert result[2] == {"amplitude": 0.5}  # Keyword args


def test_operation_call_invalid_component():
    def test_op(qubit: Qubit):
        pass

    op = Operation(test_op)

    # Try to call with wrong type
    with pytest.raises(ValueError, match="First argument to test_op must be a Qubit"):
        op("not_a_qubit")


def test_operation_call_no_args():
    def test_op(qubit: Qubit):
        pass

    op = Operation(test_op)

    # Try to call with no arguments
    with pytest.raises(
        ValueError, match="Operation test_op requires at least one argument"
    ):
        op()


def test_operation_call_multiple_args(test_qubit):
    def test_op(qubit: Qubit, arg1: float, arg2: str):
        pass

    op = Operation(test_op)
    result = op(test_qubit, 1.0, "test")

    assert result[0] == test_qubit
    assert result[1] == (1.0, "test")
    assert result[2] == {}  # No keyword args


@quam_dataclass
class TestMacro2(QubitMacro):
    """Test macro class that requires a positional argument"""

    def apply(self, required_arg, **kwargs):
        # Return inputs to verify they were passed correctly
        return (self.qubit, (required_arg,), kwargs)


def test_operation_call_out_of_order_kwargs(test_qubit):
    def test_op(qubit: Qubit, arg1: float, arg2: str = "default"):
        pass

    # Use TestMacro2 which requires a positional argument
    macro = TestMacro2()
    test_qubit.macros["test_op"] = macro

    op = Operation(test_op)
    # Pass arg2 before arg1, making arg1 (a positional arg) into a kwarg
    result = op(test_qubit, arg2="test", required_arg=1.0)

    assert result[0] == test_qubit
    assert result[1] == (1.0,)  # arg1 as positional arg
    assert result[2] == {"arg2": "test"}  # arg2 as kwarg


def test_measure_operation(test_qubit):
    from quam.utils.qua_types import QuaVariableBool

    def measure(qubit: Qubit, **kwargs) -> QuaVariableBool:
        pass

    op = Operation(measure)

    assert op.properties.return_type == QuaVariableBool
    assert op.func == measure
