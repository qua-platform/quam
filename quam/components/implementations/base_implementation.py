from abc import ABC, abstractmethod
from quam.core.quam_classes import quam_dataclass, QuamComponent


__all__ = ["BaseImplementation"]


@quam_dataclass
class BaseImplementation(QuamComponent, ABC):
    id: str

    @abstractmethod
    def apply(self, *args, **kwargs):
        """Applies the operation"""
        pass
