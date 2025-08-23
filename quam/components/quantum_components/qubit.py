from collections import UserDict
from collections.abc import Iterable
from typing import Dict, List, Optional, Union, TYPE_CHECKING, Any
from dataclasses import field

from qm import qua
from qm.qua import align

from quam.components.channels import Channel
from quam.components.pulses import Pulse
from quam.components.quantum_components import QuantumComponent
from quam.core import quam_dataclass
from quam.utils import string_reference as str_ref

if TYPE_CHECKING:
    from quam.components.macro import QubitMacro

    MacroType = QubitMacro
else:
    MacroType = Any


__all__ = ["Qubit"]


@quam_dataclass
class Qubit(QuantumComponent):
    id: Union[str, int] = "#./inferred_id"
    macros: Dict[str, MacroType] = field(default_factory=dict)

    @property
    def inferred_id(self) -> Union[str, int]:
        if not str_ref.is_reference(self.get_raw_value("id")):
            return self.id
        elif self.parent is not None:
            name = self.parent.get_attr_name(self)
            return name
        else:
            raise AttributeError(
                f"Cannot infer id of {self} because it is not attached to a parent"
            )

    @property
    def name(self) -> str:
        """Returns the name of the qubit"""
        return self.id if isinstance(self.id, str) else f"q{self.id}"

    @property
    def channels(self) -> Dict[str, Channel]:
        """Returns a dictionary of all channels of the qubit"""
        return {
            key: val
            for key, val in self.get_attrs(
                follow_references=True, include_defaults=True
            ).items()
            if isinstance(val, Channel)
        }

    def get_pulse(self, pulse_name: str) -> Pulse:
        """Returns the pulse with the given name

        Goes through all channels and returns the unique pulse with the given name.

        Raises a ValueError if the pulse is not found or if there are multiple pulses
        with the same name.
        """
        pulses = [
            pulse
            for channel in self.channels.values()
            for key, pulse in channel.operations.items()
            if key == pulse_name
        ]
        if len(pulses) == 0:
            raise ValueError(f"Pulse {pulse_name} not found")
        elif len(pulses) > 1:
            raise ValueError(f"Pulse {pulse_name} is not unique")
        else:
            return pulses[0]

    @QuantumComponent.register_macro
    def align(
        self,
        other_qubits: Optional[Union["Qubit", Iterable["Qubit"]]] = None,
        *args: "Qubit",
    ):
        """Aligns the execution of all channels of this qubit and all other qubits"""
        quantum_components = [self]

        if isinstance(other_qubits, Qubit):
            quantum_components.append(other_qubits)
        elif isinstance(other_qubits, Iterable):
            quantum_components.extend(other_qubits)
        elif other_qubits is not None:
            raise ValueError(f"Invalid type for other_qubits: {type(other_qubits)}")

        if args:
            assert all(isinstance(arg, Qubit) for arg in args)
            quantum_components.extend(args)

        channel_names = {
            ch.name for qubit in quantum_components for ch in qubit.channels.values()
        }

        align(*channel_names)

    def __matmul__(self, other):  # TODO Add QubitPair return type
        """Allows access to qubit pairs using the '@' operator, e.g. (q1 @ q2)"""
        if not isinstance(other, Qubit):
            raise ValueError(
                "Cannot create a qubit pair (q1 @ q2) with a non-qubit object, "
                f"where q1={self} and q2={other}"
            )

        if self is other:
            raise ValueError(
                "Cannot create a qubit pair with same qubit (q1 @ q1), where q1={self}"
            )

        root_quam = self.get_root()

        if root_quam is None:
            raise AttributeError(
                "Qubit pairs not found in the root component. "
                "Please add a 'qubit_pairs' attribute to the root component."
            )

        if not hasattr(root_quam, "qubit_pairs"):
            raise AttributeError(
                "Qubit pairs not found in the root component. "
                "Please add a 'qubit_pairs' attribute to the root component."
            )

        if isinstance(root_quam.qubit_pairs, UserDict):
            qubit_pairs = root_quam.qubit_pairs.values()
        else:
            qubit_pairs = root_quam.qubit_pairs

        for qubit_pair in qubit_pairs:
            if qubit_pair.qubit_control is self and qubit_pair.qubit_target is other:
                return qubit_pair
        else:
            raise ValueError(
                f"Qubit pair not found: qubit_control={self.name}, "
                f"qubit_target={other.name}"
            )
