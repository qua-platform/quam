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

    def _is_valid_setattr(
        self, attr: str, value: Any, error_on_False: bool = False
    ) -> bool:
        """Check if an attribute can be set to a value

        This will be called by __setattr__ to check if the attribute can be set to the
        given value.

        Args:
            attr: The attribute to set
            value: The value to set the attribute to
            error_on_False: If True, raise an error if the attribute cannot be set to
                the value. If False, return False if the attribute cannot be set to the
                value.

        Returns:
            True if
            - The new value is None
            - The attribute does not exist yet
            - The attribute's previous value is not a reference
            - The new value is a reference
            False otherwise, in particular if the previous value is a reference and the
            new value is not and is also not None.

        Raises:
            ValueError: If error_on_False is True and the attribute cannot be set to
                the value.
        """
        if value is None:
            return True

        try:
            original_value = self.get_unreferenced_value(attr)
        except AttributeError:
            return True

        if not self._initialized:
            return True

        if self._is_reference(original_value):
            if self._is_reference(value):
                return True

            if not error_on_False:
                return False

            raise ValueError(
                f"Cannot set attribute {attr} to {value} because it is a reference. "
                "To overwrite the reference, set the attribute to None first.\n"
                f"Object: {self}\n"
                f"Original value: {original_value}"
            )

        return True

    def __setattr__(self, attr: str, value: Any) -> None:
        self._is_valid_setattr(attr, value, error_on_False=True)

        super().__setattr__(attr, value)
