from pathlib import Path
from typing import Union, Generator, ClassVar, Any, Dict, Self, List
from dataclasses import dataclass, fields, is_dataclass

from .qua_config import build_config
from quam_components.serialisation import get_serialiser
from quam_components.utils.reference_class import ReferenceClass
from quam_components.core.quam_instantiation import instantiate_quam_base, instantiate_quam_dict_attrs


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

    def save(self):
        ...

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
            cls, contents, 
            validate_type=validate_type, 
            fix_attrs=fix_attrs
        )

    def build_config(self):
        return build_config(self)

    def iterate_quam_components(self):
        return iterate_quam_components(self)

    def get_attrs(self):
        return get_attrs(self)
    
    def to_dict(self):
        return quam_to_dict(self)

    def get_value_by_reference(self, reference: str):
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


@dataclass(kw_only=True, eq=False)
class QuamComponent(ReferenceClass):
    _quam: ClassVar[QuamBase] = None

    def get_attrs(self):
        return get_attrs(self)
    
    def to_dict(self):
        return quam_to_dict(self)

    def apply_to_config(self, config: dict) -> None:
        ...

    def _get_value_by_reference(self, reference: str):
        return self._quam.get_value_by_reference(reference)


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


def get_attrs(quam: Union[QuamBase, QuamComponent]) -> List[str]:
    if isinstance(quam, QuamDictComponent):
        return list(quam._attrs.keys())
    else:
        return [data_field.name for data_field in fields(quam)]


def quam_to_dict(quam: Any) -> Dict[str, Any]:
    if isinstance(quam, QuamDictComponent):
        return {key: quam_to_dict(val) for key, val in quam._attrs.items()}
    elif isinstance(quam, (QuamComponent, QuamBase)):
        quam_dict = {}
        attrs = quam.get_attrs()
        for attr in attrs:
            val = getattr(quam, attr)
            if isinstance(val, list):
                quam_dict[attr] = [quam_to_dict(elem) for elem in val]
            elif isinstance(val, QuamComponent):
                quam_dict[attr] = quam_to_dict(val)
            else:
                quam_dict[attr] = val
        return quam_dict
    else:
        return quam