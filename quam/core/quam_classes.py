from collections.abc import Iterable
import warnings
from pathlib import Path
from copy import deepcopy
from typing import (
    Iterator,
    Union,
    Generator,
    ClassVar,
    Any,
    Dict,
    Sequence,
    TypeVar,
    get_type_hints,
    get_origin,
    get_args,
)
from dataclasses import dataclass, fields, is_dataclass, MISSING
from collections import UserDict, UserList

from quam.serialisation import AbstractSerialiser, JSONSerialiser
from quam.utils import (
    get_dataclass_attr_annotations,
    ReferenceClass,
    string_reference,
    get_full_class_path,
)
from quam.core.quam_instantiation import instantiate_quam_class
from .qua_config_template import qua_config_template


__all__ = [
    "QuamBase",
    "QuamRoot",
    "QuamComponent",
    "QuamDict",
    "QuamList",
]


def _get_value_annotation(cls_or_obj: Union[type, object], attr: str) -> type:
    """Get the type annotation for the values in a QuamDict or QuamList.

    If the QuamDict is defined as Dict[str, int], this will return int.
    If the QuamList is defined as List[int], this will return int.
    In all other cases, this will return None.
    """
    if cls_or_obj is None or attr is None:
        return None

    cls = cls_or_obj if isinstance(cls_or_obj, type) else cls_or_obj.__class__

    annotated_attrs = get_type_hints(cls)
    if attr not in annotated_attrs:
        return None

    attr_annotation = annotated_attrs[attr]
    if get_origin(attr_annotation) == dict:
        return get_args(attr_annotation)[1]
    elif get_origin(attr_annotation) == list:
        return get_args(attr_annotation)[0]
    return None


def convert_dict_and_list(value, cls_or_obj=None, attr=None):
    if isinstance(value, dict):
        value_annotation = _get_value_annotation(cls_or_obj=cls_or_obj, attr=attr)
        return QuamDict(**value, value_annotation=value_annotation)
    elif type(value) == list:
        value_annotation = _get_value_annotation(cls_or_obj=cls_or_obj, attr=attr)
        return QuamList(value, value_annotation=value_annotation)
    else:
        return value


class ParentDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self

        if "parent" in instance.__dict__:
            return instance.__dict__["parent"]
        return None

    def __set__(self, instance, value):
        if value is None:
            instance.__dict__.pop("parent", None)
            return

        if "parent" in instance.__dict__ and instance.__dict__["parent"] is not value:
            cls = instance.__class__.__name__
            raise AttributeError(
                f"Cannot overwrite parent attribute of {cls}. "
                f"To modify {cls}.parent, first set {cls}.parent = None"
            )
        instance.__dict__["parent"] = value


class QuamBase(ReferenceClass):
    parent: ClassVar["QuamBase"] = ParentDescriptor()
    _root: ClassVar["QuamRoot"] = None

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

    def _get_parent_attr_name(self) -> str:
        """Get the attribute name of parent that matchis this object

        Raises:
            AttributeError if not found
        """
        if self.parent is None:
            raise AttributeError(
                "Could not find parent parent attribute that matches object"
                f"because object has no parent. Object={self}"
            )
        for attr_name in self.parent._get_attr_names():
            if getattr(self.parent, attr_name) is self:
                return attr_name
        else:
            raise AttributeError(
                "Could not find parent parent attribute that matches object {self}"
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

    @classmethod
    def _val_matches_attr_annotation(cls, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        The attribute type must exactly match the annotation.
        For dict and list, no additional type check of args is performed.
        """
        annotated_attrs = get_dataclass_attr_annotations(cls)
        if attr not in annotated_attrs["allowed"]:
            return False

        required_type = annotated_attrs["allowed"][attr]
        if required_type == dict or get_origin(required_type) == dict:
            return isinstance(val, (dict, QuamDict))
        elif required_type == list or get_origin(required_type) == list:
            return isinstance(val, (list, QuamList))
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
                if not self._val_matches_attr_annotation(attr, val):
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

    def _is_reference(self, attr: str) -> bool:
        return string_reference.is_reference(attr)

    def _get_referenced_value(self, reference: str):
        """Get the value of an attribute by reference

        This function is used from the ReferenceClass class.

        Returns:
            The value of the attribute, or the reference if it is not a reference
        """
        if not string_reference.is_reference(reference):
            return reference

        if string_reference.is_absolute_reference(reference) and self._root is None:
            warnings.warn(
                f"No QuamRoot initialized, cannot retrieve reference {reference}"
                f" from {self.__class__.__name__}"
            )
            return reference

        try:
            return string_reference.get_referenced_value(
                self, reference, root=self._root
            )
        except ValueError as e:
            warnings.warn(str(e))
            return reference


# Type annotation for QuamRoot, can be replaced by typing.Self from Python 3.11
QuamRootType = TypeVar("QuamRootType", bound="QuamRoot")


class QuamRoot(QuamBase):
    serialiser: AbstractSerialiser = JSONSerialiser

    def __post_init__(self):
        QuamBase._root = self

    def __setattr__(self, name, value):
        converted_val = convert_dict_and_list(value, cls_or_obj=self, attr=name)
        super().__setattr__(name, converted_val)

        if isinstance(converted_val, QuamBase) and name != "parent":
            converted_val.parent = self

    def save(
        self,
        path: Union[Path, str] = None,
        content_mapping: Dict[str, str] = None,
        include_defaults: bool = False,
        ignore: Sequence[str] = None,
    ):
        serialiser = self.serialiser()
        serialiser.save(
            quam_obj=self,
            path=path,
            content_mapping=content_mapping,
            include_defaults=include_defaults,
            ignore=ignore,
        )

    def to_dict(self, follow_references=False, include_defaults=False):
        quam_dict = super().to_dict(follow_references, include_defaults)
        # QuamRoot should always add __class__ because it is generally not
        # quam.components.quam.QuAM
        quam_dict["__class__"] = get_full_class_path(self)
        return quam_dict

    @classmethod
    def load(
        cls: QuamRootType,
        filepath_or_dict: Union[str, Path, dict],
        validate_type: bool = True,
        fix_attrs: bool = True,
    ) -> QuamRootType:
        if isinstance(filepath_or_dict, dict):
            contents = filepath_or_dict
        else:
            serialiser = cls.serialiser()
            contents, _ = serialiser.load(filepath_or_dict)

        return instantiate_quam_class(
            quam_class=cls,
            contents=contents,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
        )

    def generate_config(self):
        qua_config = deepcopy(qua_config_template)

        for quam_component in self.iterate_components():
            quam_component.apply_to_config(qua_config)

        return qua_config

    def get_unreferenced_value(self, attr):
        return getattr(self, attr)


class QuamComponent(QuamBase):
    def __setattr__(self, name, value):
        converted_val = convert_dict_and_list(value, cls_or_obj=self, attr=name)
        super().__setattr__(name, converted_val)

        if isinstance(converted_val, QuamBase) and name != "parent":
            converted_val.parent = self

    def apply_to_config(self, config: dict) -> None:
        ...


@dataclass
class QuamDict(UserDict, QuamBase):
    _value_annotation: ClassVar[type] = None

    def __init__(self, dict=None, /, value_annotation: type = None, **kwargs):
        self.__dict__["data"] = {}
        self.__dict__["_value_annotation"] = value_annotation
        super().__init__(dict, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e

    def __setattr__(self, key, value):
        if key in ["data", "parent"]:
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __getitem__(self, i):
        elem = super().__getitem__(i)
        if string_reference.is_reference(elem):
            try:
                elem = self._get_referenced_value(elem)
            except ValueError as e:
                raise KeyError(str(e)) from e
        return elem

    # Overriding methods from UserDict
    def __setitem__(self, key, value):
        value = convert_dict_and_list(value)
        super().__setitem__(key, value)

        if isinstance(value, QuamBase):
            value.parent = self

    def __eq__(self, other) -> bool:
        if isinstance(other, dict):
            return self.data == other
        return super().__eq__(other)

    # QuAM methods
    def _get_attr_names(self):
        return list(self.data.keys())

    def get_attrs(
        self, follow_references=False, include_defaults=True
    ) -> Dict[str, Any]:
        # TODO implement reference kwargs
        return self.data

    def _val_matches_attr_annotation(self, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        Called by QuamDict.to_dict to determine whether to add the __class__ key.
        For the QuamDict, we compare the type to the _value_annotation.
        """
        if isinstance(val, (QuamDict, QuamList)):
            return True
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

    def __init__(self, *args, value_annotation: type = None):
        self._value_annotation = value_annotation

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

    def __getitem__(self, i):
        elem = super().__getitem__(i)
        if isinstance(i, slice):
            # This automatically gets the referenced values
            return list(elem)

        if string_reference.is_reference(elem):
            elem = self._get_referenced_value(elem)
        return elem

    def __setitem__(self, i, item):
        converted_item = convert_dict_and_list(item)
        super().__setitem__(i, converted_item)

        if isinstance(converted_item, QuamBase):
            converted_item.parent = self

    def __iadd__(self, other: Iterable):
        converted_other = [convert_dict_and_list(elem) for elem in other]
        return super().__iadd__(converted_other)

    def append(self, item: Any) -> None:
        converted_item = convert_dict_and_list(item)

        if isinstance(converted_item, QuamBase):
            converted_item.parent = self

        return super().append(converted_item)

    def insert(self, i: int, item: Any) -> None:
        converted_item = convert_dict_and_list(item)

        if isinstance(converted_item, QuamBase):
            converted_item.parent = self

        return super().insert(i, converted_item)

    def extend(self, iterable: Iterator) -> None:
        converted_iterable = [convert_dict_and_list(elem) for elem in iterable]
        for converted_item in converted_iterable:
            if isinstance(converted_item, QuamBase):
                converted_item.parent = self

        return super().extend(converted_iterable)

    # Quam methods
    def _val_matches_attr_annotation(self, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        Called by QuamList.to_dict to determine whether to add the __class__ key.
        For the QuamList, we compare the type to the _value_annotation.
        """
        if isinstance(val, (QuamDict, QuamList)):
            return True
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
                if not self._val_matches_attr_annotation(val=val, attr=None):
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
