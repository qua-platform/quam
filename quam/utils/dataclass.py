import dataclasses
from dataclasses import dataclass, fields, is_dataclass
import functools
import sys
import warnings
from typing import Dict, Union, ClassVar, get_type_hints


__all__ = ["patch_dataclass", "get_dataclass_attr_annotations"]


class REQUIRED:
    """Flag used by `quam_dataclass` when a required dataclass arg needs a kwarg"""

    ...


def get_dataclass_attr_annotations(
    cls_or_obj: Union[type, object],
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
    annotated_attrs.pop("config_settings", None)
    annotated_attrs.pop("_value_annotation", None)
    annotated_attrs.pop("_initialized", None)

    attr_annotations = {"required": {}, "optional": {}}
    for attr, attr_type in annotated_attrs.items():
        if getattr(attr_type, "__origin__", None) == ClassVar:
            continue
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


def handle_inherited_required_fields(cls):
    """Adds a default REQUIRED flag for dataclass fields when necessary

    see quam_dataclass docs for details
    """
    if not is_dataclass(cls):
        return

    # Check if dataclass has fields with default value
    optional_fields = [
        field.name
        for field in dataclasses.fields(cls)
        if dataclass_field_has_default(field)
    ]
    if not optional_fields:
        # All fields of the dataclass are required, we don't have to handle situations
        # where the parent class has fields with default values and the subclass has
        # required fields.
        return

    # Check if class (not parents) has required fields
    for attr, attr_type in cls.__annotations__.items():
        if attr in cls.__dict__:
            continue
        if attr in optional_fields:
            continue
        if getattr(attr_type, "__origin__", None) is ClassVar:
            continue
        setattr(cls, attr, REQUIRED)


def _quam_patched_dataclass(cls=None, kw_only: bool = False, eq: bool = True):
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
        return functools.partial(_quam_patched_dataclass, kw_only=kw_only, eq=eq)

    handle_inherited_required_fields(cls)

    post_init_method = getattr(cls, "__post_init__", None)

    def __post_init__(self, *args, **kwargs):
        with warnings.catch_warnings():  # Ignore warnings of failed references
            warnings.filterwarnings("ignore", category=UserWarning)
            for f in fields(self):
                if getattr(self, f.name, None) is REQUIRED:
                    raise TypeError(
                        f"Please provide {cls.__name__}.{f.name} as it is a"
                        " required arg"
                    )

        if post_init_method is not None:
            post_init_method(self, *args, **kwargs)

    cls.__post_init__ = __post_init__
    cls_dataclass = dataclass(cls, eq=False)

    return cls_dataclass


def patch_dataclass(module_name):
    """Patch Python dataclass within a file to allow subclasses have args

    Note:
        Patch is only applied when Python < 3.10.

    Note:
        This function should be called at the top of a file, before dataclasses are
        defined:
        ```
        patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10
        ```

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

    Note:
        The python dataclass is patched in a non-standard way by calling `setattr`
        on the module. This is done to ensure that the patch is not recognized by any
        static analysis tools, such as mypy. This is necessary as mypy otherwise will
        no longer recognize the dataclass as a dataclass.
    """
    DeprecationWarning(
        "patch_dataclass is deprecated and will be removed in QuAM v1.0. "
        "Please use 'from quam.core import quam_dataclass' as a decorator instead of "
        "the regular Python dataclass."
    )
    if sys.version_info.minor < 10:
        setattr(sys.modules[module_name], "dataclass", _quam_patched_dataclass)
