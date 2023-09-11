from dataclasses import dataclass

from quam_components import QuamComponent
from quam_components.components.general import IQChannel, SingleChannel


__all__ = ["Transmon"]


@dataclass(kw_only=True, eq=False)
class Transmon(QuamComponent):
    id: int

    frequency: float = None

    xy: IQChannel = None
    z: SingleChannel = None

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"
