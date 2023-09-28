from typing import Any
from quam_components.utils.string_reference import is_reference


__all__ = ["ReferenceClass"]


class ReferenceClass:
    """Class whose attributes can by references to other attributes"""

    def _get_referenced_value(self, __name: str) -> Any:
        """Get the value of an attribute by reference

        This function should generally be overwritten by subclasses
        """
        return __name[1:]

    def get_unreferenced_value(self, attr: str) -> bool:
        """Check if an attribute is a reference"""
        return super().__getattribute__(attr)

    def __getattribute__(self, __name: str) -> Any:
        attr_val = super().__getattribute__(__name)

        if is_reference(attr_val):
            return self._get_referenced_value(attr_val)
        else:
            return attr_val
