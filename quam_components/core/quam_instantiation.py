from __future__ import annotations
import typing
from typing import TYPE_CHECKING, Dict, get_type_hints, Any
from dataclasses import MISSING
from typeguard import check_type, TypeCheckError
from inspect import isclass

if TYPE_CHECKING:
    from quam_components.core import QuamBase, QuamComponent


def get_dataclass_attr_annotations(cls: type) -> Dict[str, Dict[str, type]]:
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


def validate_obj_type(elem, required_type: type, str_repr: str = "") -> None:
    """Validate whether the object is an instance of the correct type

    References (strings starting with ":") are not checked.
    None is always allowed.

    Args:
        elem: The object to validate the type of.
        required_type: The required type of the object.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        None

    Raises:
        TypeError if the type of the attribute is not the required type
    """
    # Do not check type if the value is a reference
    if isinstance(elem, str) and elem.startswith(":"):
        return
    if elem is None:
        return

    try:
        check_type(elem, required_type)
    except TypeCheckError as e:
        raise TypeError(
            f"Wrong type type({str_repr})={type(elem)} != {required_type}"
        ) from e


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
    from quam_components.core import QuamComponent  # noqa: F811

    if typing.get_origin(required_type) == dict:
        required_subtype = typing.get_args(required_type)[1]
    else:
        required_subtype = None

    instantiated_attr_dict = {}
    for attr_name, attr_val in attr_dict.items():
        if not required_subtype:
            instantiated_attr_dict[attr_name] = attr_val
            continue

        if issubclass(required_subtype, QuamComponent):
            instantiated_attr = instantiate_quam_class(
                required_subtype,
                attr_val,
                fix_attrs=fix_attrs,
                validate_type=validate_type,
                str_repr=f"{str_repr}[{attr_name}]",
            )
        else:
            instantiated_attr = attr_val
        # Add custom __class__ QuamComponent logic here

        validate_obj_type(instantiated_attr, required_subtype, str_repr=str_repr)

        instantiated_attr_dict[attr_name] = instantiated_attr

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
    from quam_components.core import QuamComponent  # noqa: F811

    if typing.get_origin(required_type) == list:
        required_subtype = typing.get_args(required_type)[0]
    else:
        required_subtype = None

    instantiated_attr_list = []
    for k, attr_val in enumerate(attr_list):
        if not required_subtype:
            instantiated_attr_list.append(attr_val)
            continue

        if issubclass(required_subtype, QuamComponent):
            instantiated_attr = instantiate_quam_class(
                required_subtype,
                attr_val,
                fix_attrs=fix_attrs,
                validate_type=validate_type,
                str_repr=f"{str_repr}[{k}]",
            )
        else:
            instantiated_attr = attr_val
        # Add custom __class__ QuamComponent logic here

        validate_obj_type(instantiated_attr, required_subtype, str_repr=str_repr)

        instantiated_attr_list.append(instantiated_attr)

    return instantiated_attr_list


def instantiate_attr(
    attr_val,
    required_type: type,
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
        attr_val: The attribute to instantiate.
        required_type: The required type of the attribute.
        fix_attrs: Whether to only allow attributes that have been defined in the class
            Only included because it's passed on when instantiating QuamComponents.
        validate_type: Whether to validate the type of the attributes.
            If True, a TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        The instantiated attribute.
    """
    from quam_components.core import QuamComponent  # noqa: F811

    if isinstance(attr_val, str) and attr_val.startswith(":"):
        # Value is a reference, add without instantiating
        return attr_val

    if attr_val is None:
        return attr_val

    if isclass(required_type) and issubclass(required_type, QuamComponent):
        instantiated_attr = instantiate_quam_class(
            quam_class=required_type,
            contents=attr_val,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
    elif isinstance(attr_val, dict) or typing.get_origin(required_type) == dict:
        instantiated_attr = instantiate_attrs_from_dict(
            attr_dict=attr_val,
            required_type=required_type,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
    elif isinstance(attr_val, list) or typing.get_origin(required_type) == list:
        instantiated_attr = instantiate_attrs_from_list(
            attr_list=attr_val,
            required_type=required_type,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
            str_repr=str_repr,
        )
    elif typing.get_origin(required_type) == typing.Union:
        assert all(
            t in [str, int, float, bool] for t in typing.get_args(required_type)
        ), "Currently only Union[str, int, float, bool] is supported"
        instantiated_attr = attr_val
    elif typing.get_origin(required_type) is not None and validate_type:
        raise TypeError(
            f"Instantiation for type {required_type} in {str_repr} not implemented"
        )
    else:
        instantiated_attr = attr_val

    if validate_type:
        # TODO Add logic that required attributes cannot be None
        validate_obj_type(
            elem=instantiated_attr,
            required_type=required_type,
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
        attr_annotations: The attributes of the QuamComponent or QuamDictComponent
            together with their types. Grouped into "required", "optional" and "allowed"
        contents: The attr contents of the QuamRoot, QuamComponent or QuamDictComponent.
        fix_attrs: Whether to only allow attributes that have been defined in the
            class definition. If False, any attribute can be set.
            QuamDictComponents are never fixed.
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

    Returns:
        A dictionary where each element has been instantiated if it is a QuamComponent
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

        instantiated_attr = instantiate_attr(
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
            QuamDictComponents are never fixed.
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        str_repr: A string representation of the object, used for error messages.

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

    instantiated_attrs = instantiate_attrs(
        attr_annotations=attr_annotations,
        contents=contents,
        fix_attrs=fix_attrs,
        validate_type=validate_type,
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
