from typing import List

from quam_components.core import QuamBase
from .general import *
from .superconducting_qubits import *
from .resonators import *


__all__ = ["QuAM"]


class QuAM(QuamBase):
    mixers: List[Mixer]
    qubits: List[Transmon]
    resonators: List[ReadoutResonator]