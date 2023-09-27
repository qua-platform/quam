from typing import Any, Dict, Sequence, Tuple


__all__ = ["ReferenceClass", "StringReference"]


class ReferenceClass:
    """Class whose attributes can by references to other attributes"""

    _references: Dict[str, str] = None  # Overwritten during __init__

    @staticmethod
    def _str_is_reference(__value: str) -> bool:
        return __value.startswith(":")

    def _get_referenced_value(self, __name: str) -> Any:
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
        return self._get_referenced_value(reference)


class StringReference:
    @staticmethod
    def is_reference(string: str) -> bool:
        if not isinstance(string, str):
            return False
        if not string.startswith(":"):
            return False
        return True

    @staticmethod
    def is_absolute_reference(string: str) -> bool:
        if not StringReference.is_reference(string):
            return False
        if string.startswith(":."):
            return False
        return True

    @staticmethod
    def _split_next_attribute(
        string: str, splitters: Sequence[str] = ".["
    ) -> Tuple[str, str]:
        """Get the next attribute of a reference string, i.e. until a splitter

        A splitter is usually either a dot or an opening square bracket

        Args:
            string: string to split
            splitters: a sequence of characters to split on, e.g. "." and "["

        Returns:
            A tuple consisting of:
            - A string of the next attribute, i.e. until the first splitter
            - The remaining string from the first splitter
        """
        # Determine the next splitter, either a dot or square brackets []
        splitters = {}
        for splitter in [".", "["]:
            try:
                splitters[splitter] = string.index(splitter)
            except ValueError:
                splitters[splitter] is None

        if set(splitters.values()) == {None}:
            return string, ""

        next_splitter = min(key for key, val in splitters.items() if val is not None)
        splitter_idx = splitters[next_splitter]
        return string[:splitter_idx], string[splitter_idx:]

    @classmethod
    def _get_relative_reference_value(cls, obj, string: str) -> Any:
        string = string.lstrip(":")

        if not string:
            return obj
        if string.startswith("../"):
            return cls._get_relative_reference_value(obj.parent, string[3:])
        elif string.startswith("./"):
            return cls._get_relative_reference_value(obj, string[2:])
        elif string.startswith("["):
            close_idx = string.index("]")
            key = string[1:close_idx]
            return cls._get_relative_reference_value(obj[key], string[close_idx + 1 :])
        elif string.startswith("."):
            string = string[1:]

        next_attr, remaining_string = cls._split_next_attribute(string)

        return cls._get_relative_reference_value(obj[next_attr], remaining_string)

    @classmethod
    def get_referenced_value(cls, obj, string: str, root=None) -> Any:
        if not StringReference.is_reference(string):
            raise ValueError(f"String {string} is not a reference")

        if StringReference.is_absolute_reference(string):
            obj = root

        try:
            return cls._get_relative_reference_value(obj, string)
        except (AttributeError, KeyError):
            raise ValueError(f"String {string} is not a valid reference")
