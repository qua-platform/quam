from __future__ import annotations
from typing import Union, Dict, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from quam.core import QuamRoot, QuamComponent


class AbstractSerialiser:
    def save(
        self,
        path: Union[Path, str],
        quam_obj: Union[QuamRoot, QuamComponent],
        component_mapping: Dict[str, str] = None,
    ):
        raise NotImplementedError

    def load(
        self,
        path: Union[Path, str] = None,
    ):
        raise NotImplementedError
