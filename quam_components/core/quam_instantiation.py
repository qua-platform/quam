from typing import TYPE_CHECKING, Union, Sequence
from typeguard import check_type, TypeCheckError

if TYPE_CHECKING:
    from quam_components.core import QuamBase, QuamElement


def get_class_attributes(class_dict: dict, annotated_attrs: dict):
    attr_annotations = {"required": {}, "optional": {}}
    for attr, attr_type in annotated_attrs.items():
        if attr in class_dict:
            attr_annotations["optional"][attr] = attr_type
        else:
            attr_annotations["required"][attr] = attr_type
    attr_annotations["allowed"] = {**attr_annotations["required"], **attr_annotations["optional"]}
    return attr_annotations


def instantiate_quam_attrs(attrs, contents, obj_name):
    instantiated_attrs = {}
    for key, val in contents.items():
        if key not in attrs["allowed"]:
            raise AttributeError(f"Invalid attribute {key}")
        
        required_type = attrs["allowed"][key]
        if isinstance(required_type, QuamElement):
            instantiated_val = instantiate_contents(required_type, val)
        elif isinstance(required_type, Sequence):
            required_subtype = required_type.args[0]
            if isinstance(required_subtype, QuamElement):
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
            raise TypeError(f"Invalid attribute {key} for {obj_name}") from e
        
    missing_attrs = [attr for attr in attrs["required"] if attr not in instantiated_attrs]
    if missing_attrs:
        raise AttributeError(f"Missing required attribute {missing_attrs} for {obj_name}")
    
    return instantiated_attrs


def instantiate_quam_base(quam_base: QuamBase, contents: dict):
    attr_annotations = get_class_attributes(
        class_dict=quam_base.__class__.__dict__,
        annotated_attrs=quam_base.__annotations__
    )

    instantiated_attrs = instantiate_quam_attrs(
        attr_annotations, 
        contents, 
        obj_name=quam_base.__class__.__name__
    )

    for attr, val in instantiated_attrs.items():
        setattr(quam_base, attr, val)

    return quam_base


def instantiate_quam_element(quam_element_cls: type[QuamElement], contents: dict):
    attr_annotations = get_class_attributes(
        class_dict=quam_element_cls.__dict__,
        annotated_attrs=quam_element_cls.__annotations__
    )

    instantiated_attrs = instantiate_quam_attrs(
        attr_annotations, 
        contents, 
        obj_name=quam_element_cls.__name__
    )

    quam_element = quam_element_cls(**instantiated_attrs)

    return quam_element



def instantiate_contents(obj_or_cls: Union[QuamBase, type[QuamElement]], contents: dict):
    attrs = get_class_attributes(obj_or_cls)

            
        # verify that the instantiated element is of the correct type
        
        if isinstance(obj_or_cls, QuamBase):
            setattr(obj_or_cls, key, element)
        else:
            

        return element