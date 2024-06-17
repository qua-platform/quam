from typing import Dict, Any
from dataclasses import field

from quam.core import quam_dataclass, QuamComponent
from .gates.single_qubit_gates import SingleQubitGate
from .gates.two_qubit_gates import TwoQubitGate


__all__ = ["Qubit"]


@quam_dataclass
class Qubit(QuamComponent):
    id: str
    gates: Dict[str, SingleQubitGate] = field(default_factory=dict)

    def __matmul__(self, other):
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