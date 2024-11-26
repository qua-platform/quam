from quam.core.quam_classes import quam_dataclass, QuamComponent


__all__ = ["BaseOperation"]


@quam_dataclass
class BaseOperation(QuamComponent):
    id: str
