from typing import Union, Dict
from pathlib import Path

from quam_components.core import QuamRoot, QuamComponent


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
