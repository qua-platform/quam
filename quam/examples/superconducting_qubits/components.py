from dataclasses import field
from typing import Dict, Optional, Union

from quam import QuamComponent
from quam.components.channels import IQChannel, SingleChannel, InOutIQChannel
from quam.core import QuamRoot, quam_dataclass

__all__ = ["Transmon", "Quam"]


@quam_dataclass
class Transmon(QuamComponent):
    """Example QUAM component for a transmon qubit."""

    id: Union[int, str]

    xy: Optional[IQChannel] = None
    z: Optional[SingleChannel] = None

    resonator: Optional[InOutIQChannel] = None

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"


@quam_dataclass
class Quam(QuamRoot):
    """Example QUAM root component."""

    qubits: Dict[str, Transmon] = field(default_factory=dict)
    wiring: dict = field(default_factory=dict)
