import inspect
import sys
import functools
from dataclasses import dataclass, is_dataclass, fields
import dataclasses


__all__ = ["quam_dataclass", "patch_dataclass"]


class REQUIRED:
    ...


def dataclass_field_has_default(field) -> bool:
    if field.default is not dataclasses.MISSING:
        return True
    elif field.default_factory is not dataclasses.MISSING:
        return True
    return False


def dataclass_has_default_fields(cls) -> bool:
    """Check if dataclass has required fields"""
    fields = dataclasses.fields(cls)
    fields_default = any(dataclass_field_has_default(field) for field in fields)
    return fields_default


def handle_inherited_required_fields(cls):
    if not is_dataclass(cls):
        return

    # Check if dataclass has default fields
    fields_required = dataclass_has_default_fields(cls)
    if not fields_required:
        return

    # Check if class (not parents) has required fields
    attrs = inspect.signature(cls).parameters
    # Remove all attrs that are from parent classes
    attrs = {k: v for k, v in attrs.items() if k in cls.__annotations__}

    required_attrs = [
        key for key, val in attrs.items() if val.default is inspect._empty
    ]
    for attr in required_attrs:
        setattr(cls, attr, REQUIRED)


def quam_dataclass(cls=None, kw_only: bool = False, eq: bool = True):
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
    if sys.version_info.minor < 10:
        setattr(sys.modules[module_name], "dataclass", quam_dataclass)
