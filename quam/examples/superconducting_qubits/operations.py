from typing import Tuple
from qm.qua import QuaVariableType
from quam.components import Qubit, QubitPair
from quam.core import OperationsRegistry


operations_registry = OperationsRegistry()


@operations_registry.register_operation
def x(qubit: Qubit, **kwargs):
    pass


@operations_registry.register_operation
def y(qubit: Qubit, **kwargs):
    pass


@operations_registry.register_operation(
    unitary=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
)
def U(qubit: Qubit, **kwargs):
    pass


@operations_registry.register_operation
def cz(qubit_pair: QubitPair, **kwargs):
    pass


@operations_registry.register_operation
def measure(qubit: Qubit, **kwargs) -> QuaVariableType:
    pass


@operations_registry.register_operation
def align(qubits: Tuple[Qubit, ...]):
    pass
