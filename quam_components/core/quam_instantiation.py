from __future__ import annotations
import typing
from typing import TYPE_CHECKING, Dict, get_type_hints
from dataclasses import MISSING
from typeguard import check_type, TypeCheckError

if TYPE_CHECKING:
    from quam_components.core import QuamBase, QuamComponent


def get_dataclass_attr_annotations(cls: type) -> Dict[str, Dict[str, type]]:
    """Get the attributes of a dataclass that are not methods or private.

    Args:
        cls: The dataclass to get the attributes of.

    Returns:
        A dictionary where the keys are "required", "optional" and "allowed".
        The values are dictionaries with the attribute names as keys and the
        attribute types as values.
        The dictionary keys are:
            - "required": Required attributes of the class.
            - "optional": Optional attributes of the class, i.e. with a default value.
            - "allowed": allowed attributes of the class := "required" + "optional".
    """
    annotated_attrs = get_type_hints(cls)

    annotated_attrs.pop("_quam", None)
    annotated_attrs.pop("_references", None)
    annotated_attrs.pop("_skip_attrs", None)

    attr_annotations = {"required": {}, "optional": {}}
    for attr, attr_type in annotated_attrs.items():
        if hasattr(cls, attr):
            attr_annotations["optional"][attr] = attr_type
        elif attr in getattr(cls, "__dataclass_fields__", {}):
            data_field = cls.__dataclass_fields__[attr]
            if data_field.default_factory is not MISSING:
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


def validate_attr_type(instantiated_attr, required_type: type, str_repr: str = ""):
    # Do not check type if the value is a reference
    if isinstance(instantiated_attr, str) and instantiated_attr.startswith(":"):
        return
    if instantiated_attr is None:
        return

    try:
        check_type(instantiated_attr, required_type)
    except TypeCheckError as e:
        raise TypeError(
            f"Wrong type type({str_repr})={type(instantiated_attr)} != {required_type}"
        ) from e


def instantiate_quam_attrs_from_dict(
    attr_dict: dict,
    required_type: type,
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
) -> dict:
    if typing.get_origin(required_type) == dict:
        required_subtype = typing.get_args(required_type)[1]
    else:
        required_subtype = None

    instantiated_attr_list = []
    for attr_name, attr_val in attr_dict.items():
        if issubclass(required_subtype, QuamComponent):
            instantiated_attr = instantiate_quam_class(
                required_subtype,
                attr_val,
                validate_type=validate_type,
                fix_attrs=fix_attrs,
                str_repr=f"{str_repr}[{attr_name}]",
            )
        # Add custom __class__ QuamComponent logic here
        else:
            instantiated_attr = attr_val

        instantiated_attr_list[attr_name] = instantiated_attr

    return instantiated_attr_list


def instantiate_quam_attrs_from_list(
    attr_list: list,
    required_type: type,
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
) -> list:
    if typing.get_origin(required_type) == list:
        required_subtype = typing.get_args(required_type)[0]
    else:
        required_subtype = None

    instantiated_attr_list = []
    for k, attr_val in enumerate(attr_list):
        if issubclass(required_subtype, QuamComponent):
            instantiated_attr = instantiate_quam_class(
                required_subtype,
                attr_val,
                validate_type=validate_type,
                fix_attrs=fix_attrs,
                str_repr=f"{str_repr}[{k}]",
            )
        # Add custom __class__ QuamComponent logic here
        else:
            instantiated_attr = attr_val

        instantiated_attr_list.append(instantiated_attr)

    return instantiated_attr_list


def instantiate_quam_attr(
    attr_val,
    required_type: type,
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
):
    if isinstance(attr_val, str) and attr_val.startswith(":"):
        # Value is a reference, add without instantiating
        return attr_val

    if attr_val is None:
        return attr_val

    if isinstance(attr_val, dict) or typing.get_origin(required_type) == dict:
        instantiated_attr = instantiate_quam_attrs_from_dict(
            attr_dict=attr_val,
            required_type=required_type,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
    elif isinstance(attr_val, list) or typing.get_origin(required_type) == list:
        instantiated_attr = instantiate_quam_attrs_from_list(
            attr_list=attr_val,
            required_type=required_type,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
    elif typing.get_origin(required_type) is not None:
        raise TypeError(
            f"Instantiation for type {required_type} in {str_repr} not implemented"
        )
    elif issubclass(required_type, QuamComponent):
        instantiated_attr = instantiate_quam_class(
            quam_class=required_type,
            contents=attr_val,
            validate_type=validate_type,
            fix_attrs=fix_attrs,
            str_repr=str_repr,
        )
    else:
        instantiated_attr = attr_val

    if validate_type:
        validate_attr_type(
            instantiated_attr=instantiated_attr,
            required_type=required_type,
            str_repr=str_repr,
        )
    return instantiated_attr


def instantiate_quam_attrs(
    attr_annotations: Dict[str, Dict[str, type]],
    contents: dict,
    validate_type: bool = True,
    fix_attrs: bool = True,
    str_repr: str = "",
) -> dict:
    """Instantiate the attributes of a QuamComponent or QuamDictComponent

    Args:
        parent_cls: The class of the QuamRoot, QuamComponent or QuamDictComponent.
        attrs: The attributes of the QuamRoot, QuamComponent or QuamDictComponent.
        contents: The contents of the QuamRoot, QuamComponent or QuamDictComponent.
        quam_root: The QuamRoot object that the QuamRoot, QuamComponent or
            QuamDictComponent is part of.
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
            fix_attrs: Whether to only allow attributes that have been defined in the
                class definition. If False, any attribute can be set.
                QuamDictComponents are never fixed.


    Returns:
        A dictionary with the instantiated attributes of the QuamComponent or
        QuamDictComponent.
    """
    instantiated_attrs = {"required": {}, "optional": {}, "extra": {}}
    for attr_name, attr_val in contents.items():
        if attr_name not in attr_annotations["allowed"]:
            if not fix_attrs:
                instantiated_attrs["extra"][attr_name] = attr_val
                continue
            raise AttributeError(
                f"Attribute {attr_name} is not a valid attr of {str_repr}"
            )

        instantiated_attr = instantiate_quam_attr(
            attr_val=attr_val,
            required_type=attr_annotations["allowed"][attr_name],
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=f"{str_repr}.{attr_name}",
        )

        if attr_name in attr_annotations["required"]:
            instantiated_attrs["required"][attr_name] = instantiated_attr
        else:
            instantiated_attrs["optional"][attr_name] = instantiated_attr

    missing_attrs = set(attr_annotations["required"]) - set(
        instantiated_attrs["required"]
    )
    if missing_attrs:
        raise AttributeError(f"Missing required attrs {missing_attrs} for {str_repr}")

    return instantiated_attrs


def instantiate_quam_class(
    quam_class: type[QuamBase],
    contents: dict,
    validate_type: bool = True,
    fix_attrs: bool = True,
    str_repr: str = "",
) -> QuamBase:
    """Instantiate a QuamBase from a dict

    Note that any nested QuamBases are instantiated recursively

    Args:
        quam_cls: QuamBase class to instantiate
        contents: dict of attributes to instantiate the QuamBase with
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        fix_attrs: Whether to only allow attributes that have been defined in the class
            definition. If False, any attribute can be set.
            QuamDictComponents are never fixed.

    Returns:
        QuamBase instance
    """
    str_repr = f"{str_repr}.{quam_class.__name__}" if str_repr else quam_class.__name__

    if not isinstance(contents, dict):
        raise TypeError(
            f"contents must be a dict, not {type(contents)}, could not instantiate"
            f" {str_repr}"
        )
    attr_annotations = get_dataclass_attr_annotations(quam_class)

    instantiated_attrs = instantiate_quam_attrs(
        attr_annotations=attr_annotations,
        contents=contents,
        validate_type=validate_type,
        fix_attrs=fix_attrs,
        str_repr=str_repr,
    )

    quam_component = quam_class(
        **instantiated_attrs["required"], **instantiated_attrs["optional"]
    )

    if fix_attrs:
        assert not instantiated_attrs["extra"]
    else:
        for attr, val in instantiated_attrs["extra"].items():
            setattr(quam_component, attr, val)

    return quam_component
