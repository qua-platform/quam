from typing import Dict
from dataclasses import field

from quam.core import quam_dataclass, QuamComponent
from quam.components.qubit import Qubit
from quam.components.gates.two_qubit_gates import TwoQubitGate


@quam_dataclass
class QubitPair(QuamComponent):
    qubit_control: Qubit  # TODO Discuss alternatives to "control" and "target"
    qubit_target: Qubit
    gates: Dict[str, TwoQubitGate] = field(default_factory=dict)
