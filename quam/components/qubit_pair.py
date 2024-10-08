from typing import Dict
from dataclasses import field

from quam.core import quam_dataclass, QuamComponent
from quam.components.qubit import Qubit
from quam.components.gate_implementations.two_qubit_gate_implementations import (
    TwoQubitGateImplementation,
)


@quam_dataclass
class QubitPair(QuamComponent):
    qubit_control: Qubit
    qubit_target: Qubit
    gates: Dict[str, TwoQubitGateImplementation] = field(default_factory=dict)
