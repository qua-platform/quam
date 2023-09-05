from collections.abc import Iterable
from pathlib import Path
from copy import deepcopy
from typing import (
    Iterator,
    Union,
    Generator,
    ClassVar,
    Any,
    Dict,
    Self,
    get_type_hints,
    get_origin,
    get_args,
)
from dataclasses import dataclass, fields, is_dataclass, MISSING
from collections import UserDict, UserList

from quam_components.serialisation import get_serialiser
from quam_components.utils.reference_class import ReferenceClass
from quam_components.core.quam_instantiation import instantiate_quam_class
from quam_components.core.utils import (
    get_full_class_path,
    get_dataclass_attr_annotations,
)
from .qua_config_template import qua_config_template


__all__ = [
    "QuamBase",
    "QuamRoot",
    "QuamComponent",
    "QuamDict",
    "QuamList",
]


def _get_value_annotation(parent: Union[type, object], parent_attr: str) -> type:
    """Get the type annotation for the values in a QuamDict or QuamList.

    If the QuamDict is defined as Dict[str, int], this will return int.
    If the QuamList is defined as List[int], this will return int.
    In all other cases, this will return None.
    """
    annotated_attrs = get_type_hints(parent)
    if parent_attr not in annotated_attrs:
        return None

    attr_annotation = annotated_attrs[parent_attr]
    if get_origin(attr_annotation) == dict:
        return get_args(attr_annotation)[1]
    elif get_origin(attr_annotation) == list:
        return get_args(attr_annotation)[0]
    return None


def convert_dict_and_list(value, parent=None, parent_attr=None):
    if isinstance(value, dict):
        value_annotation = _get_value_annotation(parent=parent, parent_attr=parent_attr)
        return QuamDict(**value, value_annotation=value_annotation)
    elif type(value) == list:
        value_annotation = _get_value_annotation(parent=parent, parent_attr=parent_attr)
        return QuamList(value, value_annotation=value_annotation)
    else:
        return value


class QuamBase(ReferenceClass):
    def __init__(self):
        # This prohibits instantiating without it being a dataclass
        # This means that we have to subclass this class and make it a dataclass
        if not is_dataclass(self):
            if type(self) in [QuamBase, QuamComponent, QuamRoot]:
                raise TypeError(
                    f"Cannot instantiate {self.__class__.__name__} directly. "
                    "Please create a subclass and make it a dataclass."
                )
            else:
                raise TypeError(
                    f"Cannot instantiate {self.__class__.__name__}. "
                    "Please make it a dataclass."
                )

    def _get_attr_names(self):
        assert is_dataclass(self)
        return [data_field.name for data_field in fields(self)]

    def _attr_val_is_default(self, attr, val):
        if not is_dataclass(self):
            return False

        dataclass_fields = fields(self)
        if not any(field.name == attr for field in dataclass_fields):
            return False

        field = next(field for field in dataclass_fields if field.name == attr)
        if field.default is not MISSING:
            return val == field.default
        elif field.default_factory is not MISSING:
            return val == field.default_factory()

        return False

    def _attr_type_matches_annotation(self, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        The attribute type must exactly match the annotation
        """
        annotated_attrs = get_dataclass_attr_annotations(self)
        if attr not in annotated_attrs["allowed"]:
            return False

        required_type = annotated_attrs["allowed"][attr]
        return type(val) == required_type

    def get_attrs(
        self, follow_references=False, include_defaults=True
    ) -> Dict[str, Any]:
        attr_names = self._get_attr_names()

        skip_attrs = getattr(self, "_skip_attrs", [])
        attr_names = [attr for attr in attr_names if attr not in skip_attrs]

        if not follow_references:
            attrs = {attr: self.get_unreferenced_value(attr) for attr in attr_names}
        else:
            attrs = {attr: getattr(self, attr) for attr in attr_names}

        if not include_defaults:
            attrs = {
                attr: val
                for attr, val in attrs.items()
                if not self._attr_val_is_default(attr, val)
            }
        return attrs

    def to_dict(self, follow_references=False, include_defaults=False):
        attrs = self.get_attrs(
            follow_references=follow_references, include_defaults=include_defaults
        )
        quam_dict = {}
        for attr, val in attrs.items():
            if isinstance(val, QuamBase):
                quam_dict[attr] = val.to_dict(
                    follow_references=follow_references,
                    include_defaults=include_defaults,
                )
                if not self._attr_matches_annotation(self, attr, val):
                    quam_dict[attr]["__class__"] = get_full_class_path(val)
            else:
                quam_dict[attr] = val
        return quam_dict

    def iterate_components(self, skip_elems=None) -> Generator["QuamBase", None, None]:
        if skip_elems is None:
            skip_elems = []

        # We don't use "self in skip_elems" because we want to check for identity,
        # not equality. The reason is that you would otherwise have to instantiate
        # dataclasses using @dataclass(eq=False)
        in_skip_elems = any(self is elem for elem in skip_elems)
        if isinstance(self, QuamComponent) and not in_skip_elems:
            skip_elems.append(self)
            yield self

        attrs = self.get_attrs(follow_references=False, include_defaults=True)

        for attr_val in attrs.values():
            if any(attr_val is elem for elem in skip_elems):
                continue

            if isinstance(attr_val, QuamBase):
                yield from attr_val.iterate_components(skip_elems=skip_elems)

    def _get_value_by_reference(self, reference: str):
        assert reference.startswith(":")
        reference_components = reference[1:].split(".")

        elem = self
        try:
            for component in reference_components:
                if component.endswith("]"):
                    component, index_str = component[:-1].split("[")
                    elem = getattr(elem, component)[int(index_str)]
                else:
                    elem = getattr(elem, component)

        except AttributeError:
            return reference
        return elem


class QuamRoot(QuamBase):
    def __post_init__(self):
        QuamComponent._quam = self

    def __setattr__(self, name, value):
        converted_val = convert_dict_and_list(value, parent=self, parent_attr=name)
        super().__setattr__(name, converted_val)

    def save(self, path=None, content_mapping=None, include_defaults=False):
        serialiser = get_serialiser(self)
        serialiser.save(
            quam_obj=self,
            path=path,
            component_mapping=content_mapping,
            include_defaults=include_defaults,
        )

    @classmethod
    def load(
        cls,
        filepath_or_dict: Union[str, Path, dict],
        validate_type: bool = True,
        fix_attrs: bool = True,
    ) -> Self:
        if isinstance(filepath_or_dict, dict):
            contents = filepath_or_dict
        else:
            serialiser = get_serialiser(filepath_or_dict)
            contents, _ = serialiser.load(filepath_or_dict)

        return instantiate_quam_class(
            quam_class=cls,
            contents=contents,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
        )

    def build_config(self):
        qua_config = deepcopy(qua_config_template)

        for quam_component in self.iterate_components():
            quam_component.apply_to_config(qua_config)

        return qua_config

    def get_unreferenced_value(self, attr):
        return getattr(self, attr)


class QuamComponent(QuamBase):
    _quam: ClassVar[QuamRoot] = None

    def __setattr__(self, name, value):
        converted_val = convert_dict_and_list(value, parent=self, parent_attr=name)
        super().__setattr__(name, converted_val)

    def apply_to_config(self, config: dict) -> None:
        ...

    def _get_value_by_reference(self, reference: str):
        return self._quam._get_value_by_reference(reference)


@dataclass
class QuamDict(UserDict, QuamBase):
    _value_annotation: ClassVar[type] = None

    def __init__(self, dict=None, /, **kwargs):
        self.__dict__["data"] = {}
        super().__init__(dict, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key == "data":
            super().__setattr__(key, value)
        else:
            self[key] = value

    # Overriding methods from UserDict
    def __setitem__(self, key, value):
        value = convert_dict_and_list(value)
        super().__setitem__(key, value)

    # QuAM methods
    def _get_attr_names(self):
        return list(self.data.keys())

    def get_attrs(
        self, follow_references=False, include_defaults=True
    ) -> Dict[str, Any]:
        # TODO implement reference kwargs
        return self.data

    def _attr_type_matches_annotation(self, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        Called by QuamDict.to_dict to determine whether to add the __class__ key.
        For the QuamDict, we compare the type to the _value_annotation.
        """
        if self._value_annotation is None:
            return False
        return type(val) == self._value_annotation

    def _attr_val_is_default(self, attr, val):
        """Check whether the value of an attribute is the default value.

        Since a QuamDict does not have any fixed attrs, this is always False.
        """
        return False

    def get_unreferenced_value(self, attr: str) -> bool:
        return self.__getattr__(attr)

    def iterate_components(self, skip_elems=None) -> Generator["QuamBase", None, None]:
        if skip_elems is None:
            skip_elems = []

        for attr_val in self.data.values():
            if any(attr_val is elem for elem in skip_elems):
                continue

            if isinstance(attr_val, QuamBase):
                yield from attr_val.iterate_components(skip_elems=skip_elems)


@dataclass
class QuamList(UserList, QuamBase):
    _value_annotation: ClassVar[type] = None

    def __init__(self, *args):
        # We manually add elements using extend instead of passing to super()
        # To ensure that any dicts and lists get converted to QuamDict and QuamList
        super().__init__()
        if args:
            self.extend(*args)

    # Overloading methods from UserList
    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)

    def __repr__(self) -> str:
        return super().__repr__()

    def __setitem__(self, i, item):
        converted_item = convert_dict_and_list(item)
        super().__setitem__(i, converted_item)

    def __setattr__(self, i, item):
        if i == "data":
            return super().__setattr__(i, item)
        converted_item = convert_dict_and_list(item)
        super().__setattr__(i, converted_item)

    def __iadd__(self, other: Iterable) -> Self:
        converted_other = [convert_dict_and_list(elem) for elem in other]
        return super().__iadd__(converted_other)

    def append(self, item: Any) -> None:
        converted_item = convert_dict_and_list(item)
        return super().append(converted_item)

    def insert(self, i: int, item: Any) -> None:
        converted_item = convert_dict_and_list(item)
        return super().insert(i, converted_item)

    def extend(self, iterable: Iterator) -> None:
        converted_iterable = [convert_dict_and_list(elem) for elem in iterable]
        return super().extend(converted_iterable)

    # Quam methods
    def _attr_type_matches_annotation(self, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        Called by QuamList.to_dict to determine whether to add the __class__ key.
        For the QuamList, we compare the type to the _value_annotation.
        """
        if self._value_annotation is None:
            return False
        return type(val) == self._value_annotation

    def to_dict(self, follow_references=False, include_defaults=False):
        quam_list = []
        for val in self.data:
            if isinstance(val, QuamBase):
                quam_list.append(
                    val.to_dict(
                        follow_references=follow_references,
                        include_defaults=include_defaults,
                    )
                )
                if not self._attr_matches_annotation(self, val, attr=None):
                    quam_list[-1]["__class__"] = get_full_class_path(val)
            else:
                quam_list.append(val)
        return quam_list

    def iterate_components(self, skip_elems=None) -> Generator["QuamBase", None, None]:
        if skip_elems is None:
            skip_elems = []

        for attr_val in self.data:
            if any(attr_val is elem for elem in skip_elems):
                continue

            if isinstance(attr_val, QuamBase):
                yield from attr_val.iterate_components(skip_elems=skip_elems)
