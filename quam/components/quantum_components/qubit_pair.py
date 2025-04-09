from typing import Dict, TYPE_CHECKING, Any
from dataclasses import field

from quam.core import quam_dataclass
from quam.components.quantum_components import QuantumComponent, Qubit
from quam.utils import string_reference as str_ref

if TYPE_CHECKING:
    from quam.components.macro import QubitPairMacro

    MacroType = QubitPairMacro
else:
    MacroType = Any


@quam_dataclass
class QubitPair(QuantumComponent):
    id: str = "#./name"
    qubit_control: Qubit
    qubit_target: Qubit
    macros: Dict[str, MacroType] = field(default_factory=dict)

    @property
    def name(self) -> str:
        if not str_ref.is_reference(self.get_raw_value("id")):
            return self.id
        else:
            return f"{self.qubit_control.name}@{self.qubit_target.name}"

    def align(self):
        """Aligns the execution of all channels of both qubits"""
        self.qubit_control.align(self.qubit_target)
