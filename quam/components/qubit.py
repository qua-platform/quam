from typing import Dict, Union
from dataclasses import field

from quam.components.channels import Channel
from quam.core import quam_dataclass, QuamComponent
from .gate_implementations.single_qubit_gate_implementations import (
    SingleQubitGateImplementation,
)

from qm.qua._type_hinting import (
    AmpValuesType,
    QuaNumberType,
    QuaExpressionType,
    ChirpType,
    StreamType,
)


__all__ = ["Qubit"]


@quam_dataclass
class Qubit(QuamComponent):
    id: Union[str, int]
    gates: Dict[str, SingleQubitGateImplementation] = field(default_factory=dict)

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"

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
