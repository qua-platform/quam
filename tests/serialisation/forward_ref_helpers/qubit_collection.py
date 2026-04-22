"""Test helper: component holding a Dict and List of forward-referenced Resonators."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from quam.core import QuamComponent, quam_dataclass

if TYPE_CHECKING:
    from tests.serialisation.forward_ref_helpers.resonator import Resonator


@quam_dataclass
class QubitCollection(QuamComponent):
    resonator_dict: Dict[str, Resonator] = None
    resonator_list: List[Resonator] = None
