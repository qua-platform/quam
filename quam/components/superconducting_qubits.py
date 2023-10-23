from dataclasses import dataclass
from typing import Union

from quam import QuamComponent
from quam.components.channels import IQChannel, SingleChannel
from quam.components.channels import InOutIQChannel
from quam.utils import patch_dataclass

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10

__all__ = ["Transmon"]


@dataclass(kw_only=True, eq=False)
class Transmon(QuamComponent):
    """Example QuAM component for a transmon qubit."""

    id: Union[int, str]

    xy: IQChannel = None
    z: SingleChannel = None

    resonator: InOutIQChannel = None

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"
