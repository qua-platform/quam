import dataclasses
from dataclasses import dataclass, fields, is_dataclass
import functools
import sys
from typing import Dict, Union, get_type_hints


__all__ = ["patch_dataclass", "get_dataclass_attr_annotations"]


class REQUIRED:
    """Flag used by quam_dataclass when a required dataclass arg needs to have a kwarg"""

    ...


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


def dataclass_field_has_default(field: dataclasses.field) -> bool:
    """Check if a dataclass field has a default value"""
    if field.default is not dataclasses.MISSING:
        return True
    elif field.default_factory is not dataclasses.MISSING:
        return True
    return False


def dataclass_has_default_fields(cls) -> bool:
    """Check if dataclass has any default fields"""
    fields = dataclasses.fields(cls)
    fields_default = any(dataclass_field_has_default(field) for field in fields)
    return fields_default


def handle_inherited_required_fields(cls):
    """Adds a default REQUIRED flag for dataclass fields when necessary

    see quam_dataclass docs for details
    """
    if not is_dataclass(cls):
        return

    # Check if dataclass has default fields
    fields_required = dataclass_has_default_fields(cls)
    if not fields_required:
        return

    # Check if class (not parents) has required fields
    required_attrs = [attr for attr in cls.__annotations__ if attr not in cls.__dict__]
    for attr in required_attrs:
        setattr(cls, attr, REQUIRED)


def quam_dataclass(cls=None, kw_only: bool = False, eq: bool = True):
    """Patch around Python dataclass to ensure that dataclass subclassing works

    Prior to Python 3.10, it was not possible for a dataclass to be a subclass of
    another dataclass when
    - the parent dataclass has an arg with default
    - the child dataclass has a required arg

    From Python 3.10, this was fixed by including the flag @dataclass(kw_only=True).
    To ensure QuAM remains compatible with Python <3.10, we include a method to patch
    the dataclass such that it still works in the case described above.

    We achieve this by first checking if the above condition is met. If so, all the
    args without a default value receive a default REQUIRED flag. The post_init method
    is then overridden such that an error is raised whenever an attribute still has
    the REQUIRED flag after instantiation.

    The python dataclass can be overridden by calling patch_dataclass.
    """
    if cls is None:
        return functools.partial(quam_dataclass, kw_only=kw_only, eq=eq)

    handle_inherited_required_fields(cls)

    post_init_method = getattr(cls, "__post_init__", None)

    def __post_init__(self, *args, **kwargs):
        for f in fields(self):
            if getattr(self, f.name, None) is REQUIRED:
                raise TypeError(
                    f"Please provide {cls.__name__}.{f.name} as it is a required arg"
                )

        if post_init_method is not None:
            post_init_method(self, *args, **kwargs)

    cls.__post_init__ = __post_init__
    cls_dataclass = dataclass(cls, eq=False)

    return cls_dataclass


def patch_dataclass(module_name):
    """Patch Python dataclass within a file to allow subclasses have args

    Patch is only applied when Python < 3.10.
    See quam_dataclass docs for details.

    This function should be called at the top of a file, before dataclasses are defined:
    >>>  
    """
    if sys.version_info.minor < 10:
        setattr(sys.modules[module_name], "dataclass", quam_dataclass)
