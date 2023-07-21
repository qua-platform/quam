from typing import Any, Dict


class ReferenceClass:
    """Class whose attributes can by references to other attributes"""

    _references: Dict[str, str] = None  # Overwritten during __init__

    @staticmethod
    def _str_is_reference(__value: str) -> bool:
        return __value.startswith(":")

    def _get_value_by_reference(self, __name: str) -> Any:
        """Get the value of an attribute by reference

        This function should generally be overwritten by subclasses
        """
        return __name[1:]

    def get_unreferenced_value(self, attr: str) -> bool:
        """Check if an attribute is a reference"""
        return super().__getattribute__(attr)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if isinstance(__value, str) and self._str_is_reference(__value):
            # print(f"Setting reference {__name} to {__value}")
            self._references[__name] = __value

        elif __name in self._references:
            # print(f"Removing reference {__name} -> {self._references[__name]}")
            self._references.pop(__name)

        super().__setattr__(__name, __value)

    def __getattribute__(self, __name: str) -> Any:
        references = super().__getattribute__("_references")
        if references is None:
            super().__setattr__("_references", {})
            references = {}

        if __name not in references:
            return super().__getattribute__(__name)

        reference = references[__name]
        # print(f"Got reference {__name} -> {reference}")
        return self._get_value_by_reference(reference)
