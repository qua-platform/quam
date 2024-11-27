from typing import Dict
from dataclasses import field

from quam.core import quam_dataclass, QuamComponent
from quam.components.quantum_components.qubit import Qubit
from quam.components.implementations import QubitPairImplementation


@quam_dataclass
class QubitPair(QuamComponent):
    qubit_control: Qubit
    qubit_target: Qubit
    implementations: Dict[str, QubitPairImplementation] = field(default_factory=dict)

    def align(self):
        """Aligns the execution of all channels of both qubits"""
        self.qubit_control.align(self.qubit_target)
