from typing import Tuple
from qm.qua import QuaVariableType
from quam.components import Qubit, QubitPair
from quam.core import OperationsRegistry


operations_registry = OperationsRegistry()


@operations_registry.register_operation
def x(qubit: Qubit, **kwargs):
    qubit.apply("X", **kwargs)


@operations_registry.register_operation
def y(qubit: Qubit, **kwargs):
    qubit.apply("Y", **kwargs)


def U_custom(qubit: Qubit, **kwargs):
    U = qubit.get_macro(unitary=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
    U.apply(**kwargs)


@operations_registry.register_operation
def cz(qubit_pair: QubitPair, **kwargs):
    qubit_pair.apply("CZ", **kwargs)


@operations_registry.register_operation
def measure(qubit: Qubit, **kwargs) -> QuaVariableType:
    return qubit.measure(**kwargs)

# TODO Agree on function contents
@operations_registry.register_operation
def align(qubits: Tuple[Qubit, ...]):
    qubits[0].apply("align", *qubits[1:])
    # qubits[0].align(*qubits[1:])
