from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, get_type_hints
from dataclasses import MISSING
from typeguard import check_type, TypeCheckError
from inspect import isclass

if TYPE_CHECKING:
    from quam_components.core import QuamBase, QuamComponent


def get_class_attributes(cls: type) -> Dict[str, List[str]]:
    """Get the attributes of a class that are not methods or private.

    Args:
        cls: The class to get the attributes of.

    Returns:
        A dictionary with the following keys:
            - "required": A list of the required attributes of the class.
            - "optional": A list of the optional attributes of the class,
              i.e. with a default value.
            - "allowed": A list of all the allowed attributes of the class.
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


def instantiate_quam_dict_attrs(contents: dict, quam_base: QuamBase) -> dict:
    """Instantiate the attributes of a QuamDict"""
    from quam_components.core import QuamDictComponent

    instantiated_attrs = {}
    for key, val in contents.items():
        if isinstance(val, dict):
            instantiated_val = instantiate_quam_component(QuamDictComponent, val, quam_base)
        elif isinstance(val, list):
            instantiated_val = [
                (
                    elem
                    if not isinstance(elem, dict)
                    else instantiate_quam_component(QuamDictComponent, elem, quam_base)\
                )
                for elem in val
            ]
        else:
            instantiated_val = val
        instantiated_attrs[key] = instantiated_val

    return instantiated_attrs


def instantiate_quam_attrs(
    cls: type, attrs: Dict[str, List[str]], contents: dict, quam_base: QuamBase, validate_type: bool = True
) -> dict:
    """Instantiate the attributes of a QuamComponent or QuamDictComponent

    Args:
    cls: The class of the QuamBase, QuamComponent or QuamDictComponent.
    attrs: The attributes of the QuamBase, QuamComponent or QuamDictComponent.
    contents: The contents of the QuamBase, QuamComponent or QuamDictComponent.
    quam_base: The QuamBase object that the QuamBase, QuamComponent or QuamDictComponent
            is part of.
    validate_type: Whether to validate the type of the attributes.
        A TypeError is raised if an attribute has the wrong type.

    Returns:
        A dictionary with the instantiated attributes of the QuamComponent or
        QuamDictComponent.
    """
    # TODO should type checking be performed here or in the classes
    from quam_components.core import QuamComponent, QuamDictComponent

    if issubclass(cls, QuamDictComponent):
        return instantiate_quam_dict_attrs(contents, quam_base)

    instantiated_attrs = {}
    for key, val in contents.items():
        if key not in attrs["allowed"]:
            raise AttributeError(
                f"Attribute {key} is not a valid attr of {cls.__name__}"
            )

        # TODO improve type checking
        required_type = attrs["allowed"][key]
        if not isclass(required_type):  # probably part of typing module
            instantiated_val = val
        elif issubclass(required_type, QuamComponent):
            instantiated_val = instantiate_quam_component(required_type, val, quam_base, validate_type=validate_type)
        elif issubclass(required_type, List):
            required_subtype = required_type.args[0]
            if issubclass(required_subtype, QuamComponent):
                instantiated_val = [
                    instantiate_quam_component(required_subtype, v, quam_base, validate_type=validate_type)
                    for v in val
                ]
            else:
                instantiated_val = val
        elif issubclass(required_type, (dict, QuamDictComponent, Dict)):
            instantiated_val = instantiate_quam_component(QuamDictComponent, val, quam_base)
        else:
            instantiated_val = val

        # Do not check type if the value is a reference or dict
        if isinstance(instantiated_val, str) and instantiated_val.startswith(":"):
            validate_attr_type = False
        elif isinstance(instantiated_val, QuamDictComponent):
            validate_attr_type = False
        else:
            validate_attr_type = validate_type

        if validate_attr_type:
            try:
                check_type(instantiated_val, required_type)
            except TypeCheckError as e:
                raise TypeError(
                    f"Wrong type type({key})={type(instantiated_val)} !="
                    f" {required_type} for '{cls.__name__}'"
                ) from e

        instantiated_attrs[key] = instantiated_val

    missing_attrs = [
        attr for attr in attrs["required"] if attr not in instantiated_attrs
    ]
    if missing_attrs:
        raise AttributeError(
            f"Missing required attr {missing_attrs} for {cls.__name__}"
        )

    return instantiated_attrs


def instantiate_quam_base(quam_base: QuamBase, contents: dict, validate_type: bool = True) -> QuamBase:
    """Instantiate a QuamBase from a dict

    Args:
        quam_base: QuamBase instance to instantiate
        contents: dict of attributes to instantiate the QuamBase with
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.

    Returns:
        QuamBase instance
    """
    attr_annotations = get_class_attributes(cls=quam_base.__class__)

    instantiated_attrs = instantiate_quam_attrs(
        cls=quam_base.__class__,
        attrs=attr_annotations,
        contents=contents,
        quam_base=quam_base,
        validate_type=validate_type,
    )

    for attr, val in instantiated_attrs.items():
        setattr(quam_base, attr, val)

    return quam_base


def instantiate_quam_component(
    quam_component_cls: type[QuamComponent], contents: dict, quam_base: QuamBase, validate_type: bool = True
) -> QuamComponent:
    """Instantiate a QuamComponent from a dict

    Note that any nested QuamComponents are instantiated recursively

    Args:
        quam_component_cls: QuamComponent class to instantiate
        contents: dict of attributes to instantiate the QuamComponent with
        quam_base: QuamBase instance to attach the QuamComponent to
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.

    Returns:
        QuamComponent instance
    """
    if not isinstance(contents, dict):
        raise TypeError(f"contents must be a dict, not {type(contents)}, could not instantiate {quam_base}")
    attr_annotations = get_class_attributes(quam_component_cls)

    instantiated_attrs = instantiate_quam_attrs(
        cls=quam_component_cls,
        attrs=attr_annotations,
        contents=contents,
        quam_base=quam_base,
        validate_type=validate_type,
    )

    quam_component = quam_component_cls(**instantiated_attrs)
    quam_component._quam = quam_base

    return quam_component
