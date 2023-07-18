from typing import List
from dataclasses import dataclass, field

from quam_components.core import QuamRoot
from .general import *
from .superconducting_qubits import *
from .resonators import *


__all__ = ["QuAM"]


@dataclass(kw_only=True, eq=False)
class QuAM(QuamRoot):
    mixers: List[Mixer] = field(default_factory=list)
    qubits: List[Transmon] = field(default_factory=list)
    resonators: List[ReadoutResonator] = field(default_factory=list)
    local_oscillators: List[LocalOscillator] = field(default_factory=list)
    wiring: dict = field(default_factory=dict)
