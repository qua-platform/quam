from pathlib import Path
from typing import Union, Generator, ClassVar, Any, Dict, Self, List
from dataclasses import dataclass, fields, is_dataclass, MISSING

from .qua_config import build_config
from quam_components.serialisation import get_serialiser
from quam_components.utils.reference_class import ReferenceClass
from quam_components.core.quam_instantiation import (
    instantiate_quam_base,
    instantiate_quam_dict_attrs,
)


__all__ = [
    "QuamBase",
    "QuamComponent",
    "QuamDictComponent",
    "iterate_quam_components",
    "get_attrs",
]


@dataclass(kw_only=True, eq=False)
class QuamBase:
    def __post_init__(self):
        QuamComponent._quam = self

    def __setattr__(self, name, value):
        if isinstance(value, dict):
            value = QuamDictComponent(**value)

        super().__setattr__(name, value)

    def save(self, path=None, content_mapping=None):
        serialiser = get_serialiser(self)
        serialiser.save(
            quam_obj=self,
            path=path,
            component_mapping=content_mapping,
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

        return instantiate_quam_base(
            cls, contents, validate_type=validate_type, fix_attrs=fix_attrs
        )

    def build_config(self):
        return build_config(self)

    def iterate_quam_components(self):
        return iterate_quam_components(self)

    def get_attrs(self, follow_references=False, include_defaults=True):
        return get_attrs(self, follow_references=follow_references, include_defaults=include_defaults)

    def to_dict(self, follow_references=False, include_defaults=False):
        return quam_to_dict(
            self, follow_references=follow_references, include_defaults=include_defaults
        )

    def _get_value_by_reference(self, reference: str):
        assert reference.startswith(":")
        reference_components = reference[1:].split(".")

        elem = self
        try:
            for component in reference_components:
                # print(f"Getting {component} from {elem}")
                if not component.endswith("]"):
                    elem = getattr(elem, component)
                else:
                    component, index_str = component.split("[")
                    index = int(index_str[:-1])

                    elem = getattr(elem, component)[index]
        except AttributeError:
            return reference
        return elem

    def get_unreferenced_value(self, attr):
        return getattr(self, attr)


@dataclass(kw_only=True, eq=False)
class QuamComponent(ReferenceClass):
    _quam: ClassVar[QuamBase] = None

    def get_attrs(self, follow_references=False, include_defaults=True):
        return get_attrs(self, follow_references=follow_references, include_defaults=include_defaults)

    def to_dict(self, follow_references=False, include_defaults=False):
        return quam_to_dict(
            self, follow_references=follow_references, include_defaults=include_defaults
        )

    def apply_to_config(self, config: dict) -> None:
        ...

    def _get_value_by_reference(self, reference: str):
        return self._quam._get_value_by_reference(reference)


class QuamDictComponent(QuamComponent):
    _attrs = {}  # TODO check if removing this raises any test errors

    def __init__(self, **kwargs):
        super().__init__()

        self._attrs = instantiate_quam_dict_attrs(kwargs)["extra"]

    def __setitem__(self, key, value):
        self._attrs[key] = value

    def __getattr__(self, key):
        try:
            return super().__getattr__(key)
        except AttributeError:
            pass

        try:
            return self._attrs[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key == "_attrs":
            super().__setattr__(key, value)
        elif key in self._attrs:
            self._attrs[key] = value
        else:
            super().__setattr__(key, value)

    def get_unreferenced_value(self, attr: str) -> bool:
        """Check if an attribute is a reference"""
        return self.__getattr__(attr)


def iterate_quam_components(
    quam: Union[QuamBase, QuamComponent], skip_elems=None
) -> Generator[QuamComponent, None, None]:
    if not is_dataclass(quam):
        return

    if skip_elems is None:
        skip_elems = []

    if isinstance(quam, QuamComponent):
        yield quam
        skip_elems.append(quam)

    attrs = get_attrs(quam)

    for attr in attrs:
        attr_val = getattr(quam, attr)
        if attr_val in skip_elems:
            continue

        if isinstance(attr_val, QuamComponent):
            yield from iterate_quam_components(attr_val, skip_elems=skip_elems)
        if isinstance(attr_val, list):
            for elem in attr_val:
                if not isinstance(elem, QuamComponent):
                    continue
                if elem in skip_elems:
                    continue
                yield from iterate_quam_components(elem, skip_elems=skip_elems)


def _attr_val_is_default(val, quam, attr):
    if not is_dataclass(quam):
        return False

    dataclass_fields = fields(quam)
    if not any(field.name == attr for field in dataclass_fields):
        return False
    
    field = next(field for field in dataclass_fields if field.name == attr)
    if field.default is not MISSING:
        return val == field.default
    elif field.default_factory is not MISSING:
        return val == field.default_factory()


def get_attrs(
    quam: Union[QuamBase, QuamComponent], follow_references=False, include_defaults=True
) -> List[str]:
    if isinstance(quam, QuamDictComponent):
        attr_names = list(quam._attrs.keys())
    else:
        attr_names = [data_field.name for data_field in fields(quam)]

    skip_attrs = getattr(quam, "_skip_attrs", [])
    attr_names = [attr for attr in attr_names if attr not in skip_attrs]

    if not follow_references:
        attrs = {attr: quam.get_unreferenced_value(attr) for attr in attr_names}
    else:
        attrs = {attr: getattr(quam, attr) for attr in attr_names}

    if not include_defaults:
        attrs = {
            attr: val
            for attr, val in attrs.items()
            if not _attr_val_is_default(val, quam, attr)
        }
    return attrs


def quam_to_dict(
    quam: Any, follow_references=False, include_defaults=False
) -> Dict[str, Any]:
    if isinstance(quam, QuamDictComponent):
        return {
            key: quam_to_dict(
                val,
                follow_references=follow_references,
                include_defaults=include_defaults,
            )
            for key, val in quam._attrs.items()
        }
    elif isinstance(quam, list):
        return [
            quam_to_dict(
                elem,
                follow_references=follow_references,
                include_defaults=include_defaults,
            )
            for elem in quam
        ]
    elif isinstance(quam, (QuamComponent, QuamBase)):
        quam_dict = {}
        attrs = quam.get_attrs(
            follow_references=follow_references, include_defaults=include_defaults
        )
        for attr, val in attrs.items():
            if isinstance(val, list):
                quam_dict[attr] = [
                    quam_to_dict(
                        elem,
                        follow_references=follow_references,
                        include_defaults=include_defaults,
                    )
                    for elem in val
                ]
            elif isinstance(val, QuamComponent):
                quam_dict[attr] = quam_to_dict(
                    val,
                    follow_references=follow_references,
                    include_defaults=include_defaults,
                )
            else:
                quam_dict[attr] = val
        return quam_dict
    else:
        return quam
