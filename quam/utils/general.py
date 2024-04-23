import importlib
import warnings
from inspect import isclass
from typing import Any, Union

from quam.utils import string_reference

from typeguard import TypeCheckError, check_type

__all__ = ["get_full_class_path", "validate_obj_type", "get_class_from_path"]


def get_full_class_path(cls_or_obj: Union[type, object]) -> str:
    """Returns the full path of a class or object, including the module name.

    Example:
    ```
    from quam.components import Mixer
    assert get_full_class_path(Mixer) == "quam.components.hardware.Mixer"
    ```

    Args:
        cls_or_obj: The class or object to get the path of.

    Returns:
        The full path of the class or object. Generally this is of the form
        "module_name.class_name".

    Warnings:
        If the module name cannot be determined, a warning is raised.
    """
    if isclass(cls_or_obj):
        class_name = cls_or_obj.__qualname__
    else:
        class_name = cls_or_obj.__class__.__qualname__

    module_name = cls_or_obj.__module__
    if module_name == "__main__" or module_name is None:
        warnings.warn(
            f"Could not determine the module of {class_name}, this may cause issues"
            " when trying to load QuAM from a file. Please ensure that all QuAM"
            " classes are defined in a Python module"
        )
        return class_name
    else:
        return f"{module_name}.{class_name}"


def validate_obj_type(
    elem: Any, required_type: type, allow_none: bool = True, str_repr: str = ""
) -> None:
    """Validate whether the object is an instance of the correct type

    References (strings starting with "#") are not checked.
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
                "Wrong object type found during validation.\n"
                f"Path: {str_repr}\n"
                f"Required type: {required_type}\n"
                f"Actual type: {type(elem)}\n"
                f"value of actual type: {elem}"
            ) from e


def get_class_from_path(class_str) -> type:
    """Extract the class from a class path.

    Example:
        ```
        from quam.components import Mixer
        assert get_class_from_path("quam.components.hardware.Mixer") == Mixer
        ```

    Args:
        class_str: The class path, e.g. "quam.components.hardware.Mixer"

    Returns:
        Class object corresponding to the class path.
    """
    try:
        module_path, class_name = class_str.rsplit(".", 1)
    except ValueError as e:
        raise ValueError(
            "Could not extract module and class name from class path, be sure that the "
            "class path is of the form '{module_name}.{class_name}'. "
            f"class_str: '{class_str}'"
        ) from e
    module = importlib.import_module(module_path)
    quam_class = getattr(module, class_name)
    return quam_class
