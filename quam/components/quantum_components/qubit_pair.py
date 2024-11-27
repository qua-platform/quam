from typing import Dict, TYPE_CHECKING, Any
from dataclasses import field

from quam.core import quam_dataclass, QuamComponent
from quam.components.quantum_components.qubit import Qubit

if TYPE_CHECKING:
    from quam.components.implementations import QubitPairImplementation

    ImplementationType = QubitPairImplementation
else:
    ImplementationType = Any


@quam_dataclass
class QubitPair(QuamComponent):
    qubit_control: Qubit
    qubit_target: Qubit
    implementations: Dict[str, ImplementationType] = field(default_factory=dict)

    def align(self):
        """Aligns the execution of all channels of both qubits"""
        self.qubit_control.align(self.qubit_target)
