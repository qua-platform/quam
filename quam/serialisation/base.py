from __future__ import annotations
from typing import Union, Dict, TYPE_CHECKING, Optional
from pathlib import Path

if TYPE_CHECKING:
    from quam.core import QuamRoot, QuamComponent


class AbstractSerialiser:
    """Base class for serialisers."""

    def save(
        self,
        path: Optional[Union[Path, str]],
        quam_obj: Union[QuamRoot, QuamComponent],
        content_mapping: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        raise NotImplementedError

    def load(
        self,
        path: Optional[Union[Path, str]] = None,
    ):
        raise NotImplementedError
