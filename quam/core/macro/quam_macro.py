from abc import ABC
from typing import Optional, Union
from quam.core.quam_classes import quam_dataclass, QuamComponent
from quam.utils import string_reference as str_ref
from quam.core.macro.base_macro import BaseMacro

__all__ = ["QuamMacro"]


@quam_dataclass
class QuamMacro(QuamComponent, BaseMacro, ABC):
    id: str = "#./inferred_id"
    fidelity: Optional[float] = None
    duration: Optional[float] = "#./inferred_duration"

    @property
    def inferred_id(self):
        if not str_ref.is_reference(self.get_raw_value("id")):
            return self.id
        elif self.parent is not None:
            name = self.parent.get_attr_name(self)
            return name
        else:
            raise AttributeError(
                f"Cannot infer id of {self} because it is not attached to a parent"
            )
        
    @property
    def inferred_duration(self) -> Optional[float]:
        """
        This property is used to get the duration of the macro (in seconds).
        It is not implemented in the base class, but can be overridden in subclasses.
        If not implemented, the macro is assumed to have no fixed duration.
        """
        return None
