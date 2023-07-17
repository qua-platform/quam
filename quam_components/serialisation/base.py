from typing import Union, Dict, TYPE_CHECKING
from pathlib import Path

# if TYPE_CHECKING:
from quam_components.core import QuamBase, QuamComponent


class AbstractSerialiser:
    def save(
        self,
        path: Union[Path, str],
        quam_obj: Union[QuamBase, QuamComponent],
        component_mapping: Dict[str, str] = None,
    ):
        raise NotImplementedError

    def load(
        self,
        path: Union[Path, str] = None,
    ):
        raise NotImplementedError
