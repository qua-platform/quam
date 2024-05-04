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
    channels: Dict[str, Channel] = field(default_factory=dict)
    octaves: Dict[str, Octave] = field(default_factory=dict)
