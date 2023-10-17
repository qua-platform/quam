from typing import List
from dataclasses import dataclass, field

from quam.core import QuamRoot
from quam.utils import patch_dataclass
from .general import *
from .superconducting_qubits import *


patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10


__all__ = ["QuAM"]


@dataclass(kw_only=True, eq=False)
class QuAM(QuamRoot):
    controller: str = "con1"
    mixers: List[Mixer] = field(default_factory=list)
    qubits: List[Transmon] = field(default_factory=list)
    resonators: List[InOutIQChannel] = field(default_factory=list)
    local_oscillators: List[LocalOscillator] = field(default_factory=list)
    wiring: dict = field(default_factory=dict)
