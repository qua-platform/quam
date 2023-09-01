from pathlib import Path
from copy import deepcopy
from typing import Iterator, Union, Generator, ClassVar, Any, Dict, Self
from dataclasses import dataclass, fields, is_dataclass, MISSING
from collections import UserList

from quam_components.serialisation import get_serialiser
from quam_components.utils.reference_class import ReferenceClass
from quam_components.core.quam_instantiation import instantiate_quam_class
from .qua_config_template import qua_config_template


__all__ = [
    "QuamBase",
    "QuamRoot",
    "QuamComponent",
    "QuamDict",
    "QuamListComponent",
]


def convert_dict_and_list(value):
    if isinstance(value, dict):
        return QuamDict(**value)
    elif isinstance(value, list):
        return QuamListComponent(value)
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
        quam_dict = {
            attr: to_dict(
                val,
                follow_references=follow_references,
                include_defaults=include_defaults,
            )
            for attr, val in attrs.items()
        }
        return quam_dict

    def iterate_components(self, skip_elems=None) -> Generator["QuamBase", None, None]:
        if skip_elems is None:
            skip_elems = []

        # We don't use "self in skip_elems" because we want to check for identity
        if isinstance(self, QuamComponent) and not any(
            self is elem for elem in skip_elems
        ):
            skip_elems.append(self)
            yield self

        attrs = self.get_attrs(follow_references=False, include_defaults=True)

        for attr_val in attrs.values():
            if any(attr_val is elem for elem in skip_elems):
                continue

            if isinstance(attr_val, QuamBase):
                yield from attr_val.iterate_components(skip_elems=skip_elems)
            elif isinstance(attr_val, (list, tuple)):
                for elem in attr_val:
                    if isinstance(elem, QuamBase):
                        yield from elem.iterate_components(skip_elems=skip_elems)

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
        converted_val = convert_dict_and_list(value)
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
        converted_val = convert_dict_and_list(value)
        super().__setattr__(name, converted_val)

    def apply_to_config(self, config: dict) -> None:
        ...

    def _get_value_by_reference(self, reference: str):
        return self._quam._get_value_by_reference(reference)


@dataclass
class QuamDict(QuamBase):
    def __init__(self, **kwargs):
        super().__init__()

        self.__dict__["_attrs"] = {}
        for key, val in kwargs.items():
            self[key] = val

    def __iter__(self):
        return iter(self._attrs)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = QuamDict(**value)
        # TODO Add logic for QuamListComponent here

        self._attrs[key] = value

    def __getitem__(self, key):
        return self._attrs[key]

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def _get_attr_names(self):
        return list(self._attrs.keys())

    def to_dict(self, follow_references=False, include_defaults=True):
        return {
            key: to_dict(
                val,
                follow_references=follow_references,
                include_defaults=include_defaults,
            )
            for key, val in self._attrs.items()
        }

    def _attr_val_is_default(self, attr, val):
        return False

    def apply_to_config(self, config: dict) -> None:
        ...

    def get_unreferenced_value(self, attr: str) -> bool:
        return self.__getattr__(attr)


@dataclass
class QuamListComponent(UserList, QuamBase):
    def __init__(self, *args):
        # TODO Figure out why this is needed
        super().__init__(*args)

    def __iter__(self) -> Iterator:
        return super().__iter__()

    def __setitem__(self, i, item):
        print(f"Setting item {i} to {item}")
        super().__setitem__(i, item)

    def __setattr__(self, i, item):
        print(f"Setting attr {i} to {item}")
        super().__setattr__(i, item)


def to_dict(
    quam: Any, follow_references=False, include_defaults=False
) -> Dict[str, Any]:
    if isinstance(quam, QuamBase):
        return quam.to_dict(
            follow_references=follow_references, include_defaults=include_defaults
        )
    elif isinstance(quam, list):
        return [
            to_dict(
                elem,
                follow_references=follow_references,
                include_defaults=include_defaults,
            )
            for elem in quam
        ]
    else:
        return quam
