from __future__ import annotations
from typing import TYPE_CHECKING, List, get_type_hints
from dataclasses import MISSING
from typeguard import check_type, TypeCheckError
from inspect import isclass

if TYPE_CHECKING:
    from quam_components.core import QuamBase, QuamElement


def get_class_attributes(cls: type):
    annotated_attrs = get_type_hints(cls)

    attr_annotations = {"required": {}, "optional": {}}
    for attr, attr_type in annotated_attrs.items():
        if hasattr(cls, attr):
            attr_annotations["optional"][attr] = attr_type
        elif attr in getattr(cls, '__dataclass_fields__', {}):
            data_field = cls.__dataclass_fields__[attr]
            if data_field.default_factory is not MISSING:
                attr_annotations["optional"][attr] = attr_type
            else:
                attr_annotations["required"][attr] = attr_type
        else:
            attr_annotations["required"][attr] = attr_type
    attr_annotations["allowed"] = {**attr_annotations["required"], **attr_annotations["optional"]}
    return attr_annotations


def instantiate_quam_attrs(attrs, contents, obj_name):
    # TODO should type checking be performed here or in the classes
    from quam_components.core import QuamElement

    instantiated_attrs = {}
    for key, val in contents.items():
        if key not in attrs["allowed"]:
            raise AttributeError(f"Invalid attribute {key}")
        
        # TODO improve type checking
        required_type = attrs["allowed"][key]
        if not isclass(required_type):  # probably part of typing module
            instantiated_val = val
        elif issubclass(required_type, QuamElement):
            instantiated_val = instantiate_quam_element(required_type, val)
        elif issubclass(required_type, List):
            required_subtype = required_type.args[0]
            if issubclass(required_subtype, QuamElement):
                instantiated_val = [
                    instantiate_quam_element(required_subtype, v) for v in val
                ]
            else:
                instantiated_val = val
        else:
            instantiated_val = val

        try:
            check_type(instantiated_val, required_type)
        except TypeCheckError as e:
            raise TypeError(
                f"Wrong type type({key})={type(instantiated_val)} != {required_type} for '{obj_name}'") from e
        
        instantiated_attrs[key] = instantiated_val
        
    missing_attrs = [attr for attr in attrs["required"] if attr not in instantiated_attrs]
    if missing_attrs:
        raise AttributeError(f"Missing required attribute {missing_attrs} for {obj_name}")
    
    return instantiated_attrs


def instantiate_quam_base(quam_base: QuamBase, contents: dict):
    attr_annotations = get_class_attributes(cls=quam_base.__class__)

    instantiated_attrs = instantiate_quam_attrs(
        attr_annotations, 
        contents, 
        obj_name=quam_base.__class__.__name__
    )

    for attr, val in instantiated_attrs.items():
        setattr(quam_base, attr, val)

    return quam_base


def instantiate_quam_element(quam_element_cls: type[QuamElement], contents: dict):
    attr_annotations = get_class_attributes(quam_element_cls)

    instantiated_attrs = instantiate_quam_attrs(
        attr_annotations, 
        contents, 
        obj_name=quam_element_cls.__name__
    )

    quam_element = quam_element_cls(**instantiated_attrs)

    return quam_element
