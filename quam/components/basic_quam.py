from typing import Dict
from dataclasses import field

from quam.core import QuamRoot, quam_dataclass
from quam.components.channels import Channel
from quam.components.octave import Octave


__all__ = [
    "BasicQuAM",
]


@quam_dataclass
class BasicQuAM(QuamRoot):
    """Basic top-level QuAM root component.

    If custom QuAM components are used, a custom QuAM root component should be created.

    Args:
        channels (Dict[str, Channel], optional): A dictionary of channels.
        octaves (Dict[str, Octave], optional): A dictionary of octaves.
    """

    channels: Dict[str, Channel] = field(default_factory=dict)
    octaves: Dict[str, Octave] = field(default_factory=dict)
