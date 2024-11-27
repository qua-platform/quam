from typing import Dict, Union
from dataclasses import field

from qm import qua

from quam.components.channels import Channel
from quam.core import quam_dataclass, QuamComponent
from quam.components.implementations import QubitImplementation


__all__ = ["Qubit"]


@quam_dataclass
class Qubit(QuamComponent):
    id: Union[str, int]
    implementations: Dict[str, QubitImplementation] = field(default_factory=dict)

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

    def align(self, *other_qubits: "Qubit"):
        """Aligns the execution of all channels of this qubit and all other qubits"""
        channel_names = [channel.name for channel in self.channels.values()]
        for qubit in other_qubits:
            channel_names.extend([channel.name for channel in qubit.channels.values()])

        qua.align(*channel_names)

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

        if not hasattr(self._root, "qubit_pairs"):
            raise AttributeError(
                "Qubit pairs not found in the root component. "
                "Please add a 'qubit_pairs' attribute to the root component."
            )

        for qubit_pair in self._root.qubit_pairs:
            if qubit_pair.qubit_control is self and qubit_pair.qubit_target is other:
                return qubit_pair
        else:
            raise ValueError(
                "Qubit pair not found: qubit_control={self.name}, "
                "qubit_target={other.name}"
            )
