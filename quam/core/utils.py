from inspect import isclass
from typing import Union, get_type_hints, Dict
import dataclasses
from typeguard import check_type, TypeCheckError
import importlib

from quam.utils import string_reference


def get_dataclass_attr_annotations(
    cls_or_obj: Union[type, object]
) -> Dict[str, Dict[str, type]]:
    """Get the attributes and annotations of a dataclass

    Args:
        cls: The dataclass to get the attributes of.

    Returns:
        A dictionary where the keys are "required", "optional" and "allowed".
            - "required": Required attributes of the class.
            - "optional": Optional attributes of the class, i.e. with a default value.
            - "allowed": allowed attributes of the class := "required" + "optional".
        For each key, the values are dictionaries with the attribute names as keys
        and the attribute types as values.
    """
    from quam.core.quam_dataclass import REQUIRED

    annotated_attrs = get_type_hints(cls_or_obj)

    annotated_attrs.pop("_root", None)
    annotated_attrs.pop("_references", None)
    annotated_attrs.pop("_skip_attrs", None)
    annotated_attrs.pop("parent", None)

    attr_annotations = {"required": {}, "optional": {}}
    for attr, attr_type in annotated_attrs.items():
        # TODO Try to combine with third elif statement
        if getattr(cls_or_obj, attr, None) is REQUIRED:  # See "patch_dataclass()"
            if attr not in getattr(cls_or_obj, "__dataclass_fields__", {}):
                attr_annotations["required"][attr] = attr_type
            else:
                field_attr = cls_or_obj.__dataclass_fields__[attr]
                if field_attr.default_factory is not dataclasses.MISSING:
                    attr_annotations["optional"][attr] = attr_type
                else:
                    attr_annotations["required"][attr] = attr_type
        elif hasattr(cls_or_obj, attr):
            attr_annotations["optional"][attr] = attr_type
        elif attr in getattr(cls_or_obj, "__dataclass_fields__", {}):
            data_field = cls_or_obj.__dataclass_fields__[attr]
            if data_field.default_factory is not dataclasses.MISSING:
                attr_annotations["optional"][attr] = attr_type
            else:
                attr_annotations["required"][attr] = attr_type
        else:
            attr_annotations["required"][attr] = attr_type
    attr_annotations["allowed"] = {
        **attr_annotations["required"],
        **attr_annotations["optional"],
    }
    return attr_annotations


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


def get_quam_class(class_str):
    module_path, class_name = class_str.rsplit(".", 1)
    module = importlib.import_module(module_path)
    quam_class = getattr(module, class_name)
    return quam_class
