import pytest
from quam.core.operation.operations_registry import OperationsRegistry
from quam.core.operation.operation import Operation
from quam.components import Qubit


def test_operations_registry_initialization():
    registry = OperationsRegistry()
    assert len(registry) == 0


def test_register_operation_basic():
    def test_op(qubit: Qubit):
        pass

    registry = OperationsRegistry()
    wrapped_op = registry.register_operation(test_op)

    # Check the operation was registered
    assert "test_op" in registry
    assert isinstance(registry["test_op"], Operation)

    # Check the wrapped operation maintains the original function's metadata
    assert wrapped_op.__name__ == "test_op"
    assert wrapped_op.__doc__ == test_op.__doc__


def test_register_operation_as_decorator():
    registry = OperationsRegistry()

    @registry.register_operation
    def test_op(qubit: Qubit):
        pass

    assert "test_op" in registry
    assert isinstance(registry["test_op"], Operation)


def test_register_multiple_operations():
    registry = OperationsRegistry()

    def op1(qubit: Qubit):
        pass

    def op2(qubit: Qubit):
        pass

    registry.register_operation(op1)
    registry.register_operation(op2)

    assert len(registry) == 2
    assert "op1" in registry
    assert "op2" in registry


def test_registered_operation_callable(test_qubit):
    registry = OperationsRegistry()

    @registry.register_operation
    def test_op(qubit: Qubit, amplitude: float = 1.0):
        pass

    # Verify the registered operation can be called and works correctly
    result = registry["test_op"](test_qubit, amplitude=0.5)

    assert result[0] == test_qubit
    assert result[1] == ()
    assert result[2] == {"amplitude": 0.5}
