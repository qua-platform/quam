from typing import Dict, TYPE_CHECKING, Any
from dataclasses import field

from quam.core import quam_dataclass
from quam.components.quantum_components import QuantumComponent, Qubit

if TYPE_CHECKING:
    from quam.components.macro import QubitPairMacro

    MacroType = QubitPairMacro
else:
    MacroType = Any


@quam_dataclass
class QubitPair(QuantumComponent):
    qubit_control: Qubit
    qubit_target: Qubit
    macros: Dict[str, MacroType] = field(default_factory=dict)

    def align(self):
        """Aligns the execution of all channels of both qubits"""
        self.qubit_control.align(self.qubit_target)
