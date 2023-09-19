import functools
from typing import List
from dataclasses import dataclass, is_dataclass, fields
import dataclasses


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


def get_required_class_attrs(cls) -> List[str]:
    return [attr for attr in cls.__annotations__ if attr not in cls.__dict__]


def handle_inherited_required_fields(cls):
    if not is_dataclass(cls):
        return

    print(f"class {cls} has parent dataclasses")

    # Check if dataclass has default fields
    fields_required = dataclass_has_default_fields(cls)
    if not fields_required:
        print(f"Parent of {cls} have no required fields")
        return

    # Check if class (not parents) has required fields
    for attr in get_required_class_attrs(cls):
        setattr(cls, attr, REQUIRED)


def quam_dataclass(cls):
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
