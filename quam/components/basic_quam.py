from typing import Dict
from dataclasses import field
import warnings
from quam.config.models import quam
from quam.core import QuamRoot, quam_dataclass
from quam.components.channels import Channel
from quam.components.octave import Octave
from quam.components.ports import FEMPortsContainer, OPXPlusPortsContainer

__all__ = [
    "BasicQuam",
    "BasicFEMQuam",
    "BasicOPXPlusQuam",
]


@quam_dataclass
class BasicQuam(QuamRoot):
    """Basic top-level QUAM root component.

    If custom QUAM components are used, a custom QUAM root component should be created.

    Args:
        channels (Dict[str, Channel], optional): A dictionary of channels.
        octaves (Dict[str, Octave], optional): A dictionary of octaves.
    """

    channels: Dict[str, Channel] = field(default_factory=dict)
    octaves: Dict[str, Octave] = field(default_factory=dict)


@quam_dataclass
class BasicFEMQuam(BasicQuam):
    """Basic QUAM root component for FEM (Frequency Encoded Multiplexing) systems.

    Extends BasicQuam with FEM-specific port configurations for quantum control hardware.

    Attributes:
        ports (FEMPortsContainer): Container for FEM-specific analog and digital ports.
    """
    ports: FEMPortsContainer = field(default_factory=FEMPortsContainer)


@quam_dataclass
class BasicOPXPlusQuam(BasicQuam):
    """Basic QUAM root component for OPX+ systems.

    Extends BasicQuam with OPX+-specific port configurations for quantum control hardware.

    Attributes:
        ports (OPXPlusPortsContainer): Container for OPX+ analog and digital ports.
    """
    ports: OPXPlusPortsContainer = field(default_factory=OPXPlusPortsContainer)


class BasicQuAM(BasicQuam):
    def __post_init__(self, *args, **kwargs):
        warnings.warn(
            "BasicQuAM is deprecated. Use BasicQuam instead.",
            DeprecationWarning,
        )
        super().__post_init__(*args, **kwargs)
