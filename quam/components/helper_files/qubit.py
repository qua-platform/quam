from __future__ import annotations
from typing import TYPE_CHECKING
from quam.core import QuamComponent, quam_dataclass


if TYPE_CHECKING:
    from quam.components.helper_files.resonator import Resonator


@quam_dataclass
class Qubit(QuamComponent):
    resonator: Resonator
