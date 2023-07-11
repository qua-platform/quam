from typing import Listk

from quam_components.core import build_config
from .general import *
from .superconducting_qubits import *
from .resonators import *

class QuAM():
    mixers: List[Mixer]
    qubits: List[Transmon]
    resonators: List[ReadoutResonator]

    def build_config(self):
        return build_config(self)