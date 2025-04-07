from typing import Dict
from dataclasses import field
import warnings
from quam.core import QuamRoot, quam_dataclass
from quam.components.channels import Channel
from quam.components.octave import Octave

__all__ = [
    "BasicQuam",
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


class BasicQuAM(BasicQuam):
    def __post_init__(self, *args, **kwargs):
        warnings.warn(
            "BasicQuAM is deprecated. Use BasicQuam instead.",
            DeprecationWarning,
        )
        super().__post_init__(*args, **kwargs)