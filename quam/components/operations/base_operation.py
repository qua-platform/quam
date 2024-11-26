from abc import ABC, abstractmethod
from quam.core.quam_classes import quam_dataclass, QuamComponent


__all__ = ["BaseOperation"]


@quam_dataclass
class BaseOperation(QuamComponent, ABC):
    id: str

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
