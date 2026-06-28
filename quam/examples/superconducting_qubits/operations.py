from typing import Tuple
from quam.utils.qua_types import QuaVariableInt
from quam.components import Qubit, QubitPair
from quam.core import OperationsRegistry

operations_registry = OperationsRegistry()


@operations_registry.register_operation
def x(qubit: Qubit, **kwargs):
    pass


@operations_registry.register_operation
def y(qubit: Qubit, **kwargs):
    pass


@operations_registry.register_operation
def Rx(qubit: Qubit, angle: float, **kwargs):
    pass


@operations_registry.register_operation
def cz(qubit_pair: QubitPair, **kwargs):
    pass


@operations_registry.register_operation
def measure(qubit: Qubit, **kwargs) -> QuaVariableInt:  # type: ignore[empty-body]
    pass


@operations_registry.register_operation
def align(qubits: Tuple[Qubit, ...]):
    pass
