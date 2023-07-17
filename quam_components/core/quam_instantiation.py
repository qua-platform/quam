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


def instantiate_quam_dict_attrs(contents: dict) -> dict:
    """Instantiate the attributes of a QuamDict"""
    from quam_components.core import QuamDictComponent

    instantiated_attrs = {"required": {}, "optional": {}, "extra": {}}
    for key, val in contents.items():
        if isinstance(val, dict):
            instantiated_val = instantiate_quam_component(QuamDictComponent, val)
        elif isinstance(val, list):
            instantiated_val = [
                (
                    elem
                    if not isinstance(elem, dict)
                    else instantiate_quam_component(QuamDictComponent, elem)
                )
                for elem in val
            ]
        else:
            instantiated_val = val
        instantiated_attrs["extra"][key] = instantiated_val

    return instantiated_attrs


def instantiate_quam_attrs(
    cls: type,
    attrs: Dict[str, List[str]],
    contents: dict,
    validate_type: bool = True,
    fix_attrs: bool = True,
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
        fix_attrs: Whether to only allow attributes that have been defined in the class
            definition. If False, any attribute can be set.
            QuamDictComponents are never fixed.


    Returns:
        A dictionary with the instantiated attributes of the QuamComponent or
        QuamDictComponent.
    """
    # TODO should type checking be performed here or in the classes
    from quam_components.core import QuamComponent, QuamDictComponent

    if issubclass(cls, QuamDictComponent):
        return instantiate_quam_dict_attrs(contents)

    instantiated_attrs = {"required": {}, "optional": {}, "extra": {}}
    for key, val in contents.items():
        if key not in attrs["allowed"]:
            if not fix_attrs:
                instantiated_attrs["extra"][key] = val
                continue
            raise AttributeError(
                f"Attribute {key} is not a valid attr of {cls.__name__}"
            )

        required_type = attrs["allowed"][key]
        if not isclass(required_type):  # probably part of typing module
            instantiated_val = val
        elif issubclass(required_type, QuamComponent):
            instantiated_val = instantiate_quam_component(
                required_type,
                val,
                validate_type=validate_type,
                fix_attrs=fix_attrs,
            )
        elif issubclass(required_type, List):
            required_subtype = required_type.args[0]
            if issubclass(required_subtype, QuamComponent):
                instantiated_val = [
                    instantiate_quam_component(
                        required_subtype,
                        v,
                        validate_type=validate_type,
                        fix_attrs=fix_attrs,
                    )
                    for v in val
                ]
            else:
                instantiated_val = val
        elif issubclass(required_type, (dict, QuamDictComponent, Dict)):
            instantiated_val = instantiate_quam_component(QuamDictComponent, val)
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

        if key in attrs["required"]:
            instantiated_attrs["required"][key] = instantiated_val
        else:
            instantiated_attrs["optional"][key] = instantiated_val

    missing_attrs = set(attrs["required"]) - set(instantiated_attrs["required"])
    if missing_attrs:
        raise AttributeError(
            f"Missing required attr {missing_attrs} for {cls.__name__}"
        )

    return instantiated_attrs


def instantiate_quam_base(
    quam_base_cls: type[QuamBase],
    contents: dict,
    validate_type: bool = True,
    fix_attrs: bool = True,
) -> QuamBase:
    """Instantiate a QuamBase from a dict

    Args:
        quam_base: QuamBase instance to instantiate
        contents: dict of attributes to instantiate the QuamBase with
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        fix_attrs: Whether to only allow attributes that have been defined in the class
            definition. If False, any attribute can be set.
            QuamDictComponents are never fixed.

    Returns:
        QuamBase instance
    """
    attr_annotations = get_class_attributes(cls=quam_base_cls)

    instantiated_attrs = instantiate_quam_attrs(
        cls=quam_base_cls,
        attrs=attr_annotations,
        contents=contents,
        validate_type=validate_type,
        fix_attrs=fix_attrs,
    )

    attrs = {**instantiated_attrs["required"], **instantiated_attrs["optional"]}
    quam_base = quam_base_cls(**attrs)

    if not fix_attrs:
        for attr, val in instantiated_attrs["extra"].items():
            setattr(quam_base, attr, val)

    for quam_component in quam_base.iterate_quam_components():
        quam_component._quam = quam_base

    return quam_base


def instantiate_quam_component(
    quam_component_cls: type[QuamComponent],
    contents: dict,
    validate_type: bool = True,
    fix_attrs: bool = True,
) -> QuamComponent:
    """Instantiate a QuamComponent from a dict

    Note that any nested QuamComponents are instantiated recursively

    Args:
        quam_component_cls: QuamComponent class to instantiate
        contents: dict of attributes to instantiate the QuamComponent with
        quam_base: QuamBase instance to attach the QuamComponent to
        validate_type: Whether to validate the type of the attributes.
            A TypeError is raised if an attribute has the wrong type.
        fix_attrs: Whether to only allow attributes that have been defined in the class
            definition. If False, any attribute can be set.
            QuamDictComponents are never fixed.

    Returns:
        QuamComponent instance
    """
    from quam_components.core import QuamDictComponent

    if not isinstance(contents, dict):
        raise TypeError(
            f"contents must be a dict, not {type(contents)}, could not instantiate"
            f" {quam_component_cls}"
        )
    attr_annotations = get_class_attributes(quam_component_cls)

    instantiated_attrs = instantiate_quam_attrs(
        cls=quam_component_cls,
        attrs=attr_annotations,
        contents=contents,
        validate_type=validate_type,
        fix_attrs=fix_attrs,
    )

    quam_component = quam_component_cls(
        **instantiated_attrs["required"], **instantiated_attrs["optional"]
    )

    if not fix_attrs:
        for attr, val in instantiated_attrs["extra"].items():
            setattr(quam_component, attr, val)
    elif isinstance(quam_component, QuamDictComponent):
        for attr, val in instantiated_attrs["extra"].items():
            quam_component._attrs[attr] = val

    return quam_component
