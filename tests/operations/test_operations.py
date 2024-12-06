import pytest
from quam.core.operation.operation import Operation
from quam.core.operation.function_properties import FunctionProperties
from quam.components import Qubit
from quam.components.macro import QubitMacro
from quam.core import quam_dataclass


@quam_dataclass
class TestMacro(QubitMacro):
    """Simple macro class for testing purposes"""

    def apply(self, *args, **kwargs):
        # Return inputs to verify they were passed correctly
        return (self.qubit, args, kwargs)


@pytest.fixture
def test_qubit():
    """Fixture providing a qubit with common test macros"""
    qubit = Qubit(id="test_qubit")

    # Add some common macros
    qubit.macros["x_gate"] = TestMacro()
    qubit.macros["test_op"] = TestMacro()

    return qubit


def test_operation_initialization():
    def sample_op(qubit: Qubit):
        pass

    op = Operation(sample_op)
    assert op.func == sample_op
    assert op.unitary is None
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
