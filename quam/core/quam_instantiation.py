from __future__ import annotations
import sys
import types
import typing
from typing import TYPE_CHECKING, Dict, Any
from inspect import isclass

from quam.utils import (
    string_reference,
    get_dataclass_attr_annotations,
    get_class_from_path,
    validate_obj_type,
    type_is_optional,
)
from .deprecations import instantiation_deprecations

if TYPE_CHECKING:
    from quam.core import QuamBase


if sys.version_info < (3, 10):
    union_types = (typing.Union,)
else:
    union_types = [typing.Union, types.UnionType]


def instantiate_attrs_from_dict(
    attr_dict: dict,
    required_type: type,
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
) -> dict:
    """Instantiate the QuamComponent attributes in a dict

    QuamComponents are only instantiated if required_type is typing.Dict and the value
    subtype is a QuamComponent. In this case, the value is instantiated as a
    QuamComponent.
    Otherwise, no QuamComponents are instantiated.

    Args:
        attr_dict: The attributes to instantiate.
        required_type: The required type of the attributes, either dict or typing.Dict.
        fix_attrs: Whether to only allow attributes that have been defined in the class
            Only included because it's passed on when instantiating QuamComponents.
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        A dictionary with the instantiated attributes.
    """
    from quam.core import QuamComponent  # noqa: F811

    if typing.get_origin(required_type) == dict:
        required_subtype = typing.get_args(required_type)[1]
    else:
        required_subtype = None

    instantiated_attr_dict = {}
    for attr_name, attr_val in attr_dict.items():
        instantiated_attr_dict[attr_name] = instantiate_attr(
            attr_val=attr_val,
            expected_type=required_subtype,
            allow_none=False,
            fix_attrs=fix_attrs,
            validate_type=validate_type if required_subtype is not None else False,
            str_repr=f'{str_repr}["{attr_name}"]',
        )

    return instantiated_attr_dict


def instantiate_attrs_from_list(
    attr_list: list,
    required_type: type,
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
) -> list:
    """Instantiate the QuamComponent attributes in a list

    QuamComponents are only instantiated if required_type is typing.List and the subtype
    is a QuamComponent. In this case, the value is instantiated as a QuamComponent.
    Otherwise, no QuamComponents are instantiated.

    Args:
        attr_list: The attributes to instantiate.
        required_type: The required type of the attributes, either list or typing.List.
        fix_attrs: Whether to only allow attributes that have been defined in the class
            Only included because it's passed on when instantiating QuamComponents.
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        A list with the instantiated attributes.
    """
    from quam.core import QuamComponent  # noqa: F811

    if typing.get_origin(required_type) == list:
        required_subtype = typing.get_args(required_type)[0]
    else:
        required_subtype = None

    instantiated_attr_list = []
    for k, attr_val in enumerate(attr_list):
        instantiated_attr_list.append(
            instantiate_attr(
                attr_val=attr_val,
                expected_type=required_subtype,
                allow_none=False,
                fix_attrs=fix_attrs,
                validate_type=validate_type if required_subtype is not None else False,
                str_repr=f"{str_repr}[{k}]",
            )
        )
    return instantiated_attr_list


def instantiate_attr(
    attr_val,
    expected_type: type,
    allow_none: bool = False,
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
):
    """Instantiate a single attribute which may be a QuamComponent

    The attribute instantiation behaviour depends on the required attribute type:
        - If the required type is a QuamComponent -> instantiate the QuamComponent
        - If the required type is a dict -> instantiate all elements of the dict
        - If the required type is a list -> instantiate all elements of the list
        - Otherwise, the attribute is not instantiated

    Note that references and None are not instantiated, nor validated.

    Args:
        attr_val: The value of the to instantiate.
        required_type: The required type of the attribute.
        allow_none: Whether None is allowed as a value even if it's the wrong type.
        fix_attrs: Whether to only allow attributes that have been defined in the class
            Only included because it's passed on when instantiating QuamComponents.
        validate_type: Whether to validate the type of the attributes.
            If True, a TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        The instantiated attribute.
    """
    from quam.core import QuamComponent  # noqa: F811

    # Convert Optional[T] to T with allow_none=True
    if type_is_optional(expected_type):
        expected_type = typing.get_args(expected_type)[0]
        allow_none = True

    if string_reference.is_reference(attr_val):
        # Value is a reference, add without instantiating
        instantiated_attr = attr_val
    elif attr_val is None:
        instantiated_attr = attr_val
    elif isclass(expected_type) and issubclass(expected_type, QuamComponent):
        instantiated_attr = instantiate_quam_class(
            quam_class=expected_type,
            contents=attr_val,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
    elif isinstance(attr_val, dict) and "__class__" in attr_val:
        instantiated_attr = instantiate_quam_class(
            quam_class=expected_type,
            contents=attr_val,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
    elif isinstance(expected_type, dict) or typing.get_origin(expected_type) == dict:
        instantiated_attr = instantiate_attrs_from_dict(
            attr_dict=attr_val,
            required_type=expected_type,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
        if typing.get_origin(expected_type) == dict:
            expected_type = dict
    elif typing.get_origin(expected_type) in union_types:
        for union_type in typing.get_args(expected_type):
            try:
                instantiated_attr = instantiate_attr(
                    attr_val=attr_val,
                    expected_type=union_type,
                    allow_none=allow_none,
                    fix_attrs=fix_attrs,
                    validate_type=validate_type,
                    str_repr=str_repr,
                )
                break
            except TypeError:
                continue
        else:
            raise TypeError(
                f"Could not instantiate {str_repr} with any of the types in {expected_type}"
            )
    elif (
        isinstance(expected_type, list)
        or typing.get_origin(expected_type) == list
        or isinstance(attr_val, list)
    ):
        instantiated_attr = instantiate_attrs_from_list(
            attr_list=attr_val,
            required_type=expected_type,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
        if typing.get_origin(expected_type) == list:
            expected_type = list
        elif typing.get_origin(expected_type) == tuple:
            instantiated_attr = tuple(instantiated_attr)
    elif typing.get_origin(expected_type) == tuple:
        if isinstance(attr_val, list):
            attr_val = tuple(attr_val)
        instantiated_attr = attr_val
    elif typing.get_origin(expected_type) == typing.Literal:
        instantiated_attr = attr_val
    elif typing.get_origin(expected_type) is not None and validate_type:
        raise TypeError(
            f"Instantiation for type {expected_type} in {str_repr} not implemented"
        )
    else:
        instantiated_attr = attr_val

    if validate_type:
        # TODO Add logic that required attributes cannot be None
        validate_obj_type(
            elem=instantiated_attr,
            required_type=expected_type,
            allow_none=allow_none,
            str_repr=str_repr,
        )
    return instantiated_attr


def instantiate_attrs(
    attr_annotations: Dict[str, Dict[str, type]],
    contents: dict,
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
) -> Dict[str, Any]:
    """Instantiate attributes if they are or contain QuamComponents

    Dictionaries and lists are instantiated recursively

    Args:
        attr_annotations: The attributes of the QuamComponent or QuamDict
            together with their types. Grouped into "required", "optional" and "allowed"
        contents: The attr contents of the QuamRoot, QuamComponent or QuamDict.
        fix_attrs: Whether to only allow attributes that have been defined in the
            class definition. If False, any attribute can be set.
            QuamDicts are never fixed.
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        A dictionary where each element has been instantiated if it is a QuamComponent
    """
    instantiated_attrs = {"required": {}, "optional": {}, "extra": {}}
    for attr_name, attr_val in contents.items():
        if attr_name == "__class__":
            continue
        if attr_name not in attr_annotations["allowed"]:
            if not fix_attrs:
                instantiated_attrs["extra"][attr_name] = attr_val
                continue
            raise AttributeError(
                f"Attribute {attr_name} is not a valid attr of {str_repr}"
            )

        if isinstance(attr_val, dict) and "__class__" in attr_val:
            expected_type = get_class_from_path(attr_val["__class__"])
        else:
            expected_type = attr_annotations["allowed"][attr_name]

        instantiated_attr = instantiate_attr(
            attr_val=attr_val,
            expected_type=expected_type,
            allow_none=attr_name not in attr_annotations["required"],
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
    fix_attrs: bool = True,
    validate_type: bool = True,
    str_repr: str = "",
) -> QuamBase:
    """Instantiate a QuamBase from a dict

    Note that any nested QuamBases are instantiated recursively

    Args:
        quam_class: QuamBase class to instantiate
        contents: dict of attributes to instantiate the QuamBase with
        fix_attrs: Whether to only allow attributes that have been defined in the class
            definition. If False, any attribute can be set.
            QuamDicts are never fixed.
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        QuamBase instance
    """
    # Add depcrecation checks
    for deprecation_rule in instantiation_deprecations:
        if deprecation_rule.match(quam_class=quam_class, contents=contents):
            quam_class, contents = deprecation_rule.apply(
                quam_class=quam_class, contents=contents
            )

    if not str_repr:
        str_repr = quam_class.__name__
    # str_repr = f"{str_repr}.{quam_class.__name__}" if str_repr else quam_class.__name__

    if "__class__" in contents:
        quam_class = get_class_from_path(contents["__class__"])

    if not isinstance(contents, dict):
        raise TypeError(
            f"contents must be a dict, not {type(contents)}, could not instantiate"
            f" {str_repr}. Contents: {contents}"
        )

    attr_annotations = get_dataclass_attr_annotations(quam_class)

    instantiated_attrs = instantiate_attrs(
        attr_annotations=attr_annotations,
        contents=contents,
        fix_attrs=fix_attrs,
        validate_type=validate_type,
        str_repr=str_repr,
    )

    quam_component = quam_class(
        **{**instantiated_attrs["required"], **instantiated_attrs["optional"]}
    )

    if fix_attrs:
        assert not instantiated_attrs["extra"]
    else:
        for attr, val in instantiated_attrs["extra"].items():
            setattr(quam_component, attr, val)

    return quam_component
