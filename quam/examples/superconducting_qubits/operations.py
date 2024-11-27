from qm.qua import QuaVariableType
from quam.components import Qubit
from quam.core import OperationsRegistry

operations_registry = OperationsRegistry()


@operations_registry.register_operation
def x(qubit: Qubit, **kwargs):
    qubit.apply("X", **kwargs)


@operations_registry.register_operation
def y(qubit: Qubit, **kwargs):
    qubit.apply("Y", **kwargs)


@operations_registry.register_operation
def cz(qubit_control: Qubit, qubit_target: Qubit, **kwargs):
    qubit_pair = qubit_control @ qubit_target
    qubit_pair.apply("CZ", **kwargs)


@operations_registry.register_operation
def measure(qubit: Qubit, **kwargs) -> QuaVariableType:
    return qubit.measure(**kwargs)


@operations_registry.register_operation
def align(*qubits: Qubit):
    qubits[0].align(*qubits[1:])
