from abc import ABC

from quam.core.macro import QuamMacro
from quam.core import quam_dataclass

from quam.components.quantum_components.qubit import Qubit


__all__ = ["QubitPairMacro"]


@quam_dataclass
class QubitPairMacro(QuamMacro, ABC):
    @property
    def qubit_pair(self):  # TODO Add QubitPair return type
        from quam.components.quantum_components.qubit_pair import QubitPair

        if isinstance(self.parent, QubitPair):
            return self.parent
        elif hasattr(self.parent, "parent") and isinstance(
            self.parent.parent, QubitPair
        ):
            return self.parent.parent
        else:
            raise AttributeError(
                "TwoQubitGate is not attached to a QubitPair. 2Q_gate: {self}"
            )

    @property
    def qubit_control(self) -> Qubit:
        return self.qubit_pair.qubit_control

    @property
    def qubit_target(self) -> Qubit:
        return self.qubit_pair.qubit_target
