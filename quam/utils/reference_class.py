from typing import Any, ClassVar


__all__ = ["ReferenceClass"]


class ReferenceClass:
    """Class whose attributes can by references to other attributes"""

    _initialized: ClassVar[bool] = False

    def __post_init__(self) -> None:
        """Post init function"""
        self._initialized = True

    def _get_referenced_value(self, attr: str) -> Any:
        """Get the value of an attribute by reference

        This function should generally be overwritten by subclasses
        """
        raise NotImplementedError

    def _is_reference(self, attr: str) -> bool:
        """Check if an attribute is a reference

        This function should generally be overwritten by subclasses
        """
        raise NotImplementedError

    def get_unreferenced_value(self, attr: str) -> bool:
        """Check if an attribute is a reference"""
        return super().__getattribute__(attr)

    def __getattribute__(self, attr: str) -> Any:
        attr_val = super().__getattribute__(attr)

        if attr in ["_is_reference", "_get_referenced_value", "__post_init__"]:
            return attr_val

        try:
            if self._is_reference(attr_val):
                return self._get_referenced_value(attr_val)
            return attr_val
        except Exception:
            return attr_val

    def __setattr__(self, attr: str, value: Any) -> None:
        if value is None:
            return super().__setattr__(attr, value)

        try:
            original_value = super().__getattribute__(attr)
        except AttributeError:
            return super().__setattr__(attr, value)

        if not self._initialized:
            return super().__setattr__(attr, value)

        if self._is_reference(original_value) and value is not None:
            raise ValueError(
                f"Cannot set attribute {attr} to {value} because it is a reference. "
                "To overwrite the reference, set the attribute to None first.\n"
                f"Object: {self}\n"
                f"Original value: {original_value}"
            )

        super().__setattr__(attr, value)
