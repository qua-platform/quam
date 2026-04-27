"""Test helper: Resonator component that circularly references Qubit via TYPE_CHECKING."""
from __future__ import annotations

from typing import TYPE_CHECKING

from quam.core import QuamComponent, quam_dataclass

if TYPE_CHECKING:
    from tests.serialisation.forward_ref_helpers.qubit import Qubit


@quam_dataclass
class Resonator(QuamComponent):
    qubit: Qubit
