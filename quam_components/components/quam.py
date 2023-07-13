from typing import List
from dataclasses import dataclass

from quam_components.core import QuamBase
from .general import *
from .superconducting_qubits import *
from .resonators import *


__all__ = ["QuAM"]


@dataclass
class QuAM(QuamBase):
    mixers: List[Mixer]
    qubits: List[Transmon]
    resonators: List[ReadoutResonator]

    def build_config(self):
        return build_config(self)