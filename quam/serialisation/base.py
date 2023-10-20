from __future__ import annotations
from typing import Union, Dict, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from quam.core import QuamRoot, QuamComponent


class AbstractSerialiser:
    """Base class for serialisers."""
    def save(
        self,
        path: Union[Path, str],
        quam_obj: Union[QuamRoot, QuamComponent],
        content_mapping: Dict[str, str] = None,
    ):
        raise NotImplementedError

    def load(
        self,
        path: Union[Path, str] = None,
    ):
        raise NotImplementedError
