import importlib
from inspect import isclass
from typing import Union

from quam.utils import string_reference

from typeguard import TypeCheckError, check_type

__all__ = ["get_full_class_path", "validate_obj_type", "get_class_from_path"]


def get_full_class_path(cls_or_obj: Union[type, object]) -> str:
    """Returns the full path of a class or object, including the module name."""
    if isclass(cls_or_obj):
        class_name = cls_or_obj.__qualname__
    else:
        class_name = cls_or_obj.__class__.__qualname__

    module_name = cls_or_obj.__module__
    if module_name == "__main__" or module_name is None:
        return class_name
    else:
        return f"{module_name}.{class_name}"


def validate_obj_type(
    elem, required_type: type, allow_none: bool = True, str_repr: str = ""
) -> None:
    """Validate whether the object is an instance of the correct type

    References (strings starting with ":") are not checked.
    None is always allowed.

    Args:
        elem: The object to validate the type of.
        required_type: The required type of the object.
        allow_none: Whether None is allowed as a value even if it's the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        None

    Raises:
        TypeError if the type of the attribute is not the required type
    """
    # Do not check type if the value is a reference
    if string_reference.is_reference(elem):
        return
    if elem is None and allow_none:
        return
    try:
        check_type(elem, required_type)
    except TypeCheckError as e:
        if elem is None:
            raise TypeError(
                f"None is not allowed for required attribute {str_repr}"
            ) from e
        else:
            raise TypeError(
                f"Wrong type type({str_repr})={type(elem)} != {required_type}"
            ) from e


def get_class_from_path(class_str):
    module_path, class_name = class_str.rsplit(".", 1)
    module = importlib.import_module(module_path)
    quam_class = getattr(module, class_name)
    return quam_class
