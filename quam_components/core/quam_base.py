from pathlib import Path
import collections
from typing import Union, Generator, ClassVar
from dataclasses import dataclass, fields, is_dataclass

from .qua_config import build_config
from quam_components.serialisers import get_serialiser
from quam_components.utils.reference_class import ReferenceClass
from quam_components.core.quam_instantiation import instantiate_quam_base


__all__ = ["QuamBase", "QuamElement", "QuamDictElement", "iterate_quam_elements"]


@dataclass(kw_only=True, eq=False)
class QuamBase:
    def __post_init__(self, filepath=None):
        self.filepath = filepath

        if self.filepath is not None:
            self.serialiser = get_serialiser(self.filepath)
            self.load()
        else:
            self.serialiser = None

        QuamElement._quam = self

    def save(self):
        ...

    def load(self, filepath_or_dict: Union[str, Path, dict] = None):
        if isinstance(filepath_or_dict, (str, Path)):
            contents = self.serialiser.load(filepath_or_dict)
        elif isinstance(filepath_or_dict, dict):
            contents = filepath_or_dict
        elif filepath_or_dict is None and self.filepath is not None:
            contents = self.serialiser.load(self.filepath)

        instantiate_quam_base(self, contents)

    def build_config(self):
        return build_config(self)

    def iterate_quam_elements(self):
        return iterate_quam_elements(self)

    def get_value_by_reference(self, reference: str):
        assert reference.startswith(":")
        reference_components = reference[1:].split(".")

        elem = self
        for component in reference_components:
            # print(f"Getting {component} from {elem}")
            if not component.endswith("]"):
                elem = getattr(elem, component)

            else:
                component, index_str = component.split("[")
                index = int(index_str[:-1])

                elem = getattr(elem, component)[index]
        return elem


@dataclass(kw_only=True, eq=False)
class QuamElement(ReferenceClass):
    controller: str = "con1"

    _quam: ClassVar[QuamBase] = None

    def apply_to_config(self, config: dict) -> None:
        ...

    def _get_value_by_reference(self, reference: str):
        return self._quam.get_value_by_reference(reference)
    

class QuamDictElement(QuamElement):
    _attrs = {}

    def __init__(self, **kwargs):
        super().__init__()

        self._attrs = kwargs

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
        if key == '_attrs':
            super().__setattr__(key, value)
        elif key in self._attrs:
            self._attrs[key] = value
        else:
            super().__setattr__(key, value)


def iterate_quam_elements(quam: Union[QuamBase, QuamElement], skip_elems=None) -> Generator[QuamElement, None, None]:
    if not is_dataclass(quam):
        return
    
    if skip_elems is None:
        skip_elems = []

    if isinstance(quam, QuamElement):
        yield quam
        skip_elems.append(quam)

    if isinstance(quam, QuamDictElement):
        obj_data_values = quam._attrs.values()
    else:
        obj_data_values = [data_field.name for data_field in fields(quam)]

    for attr_val in obj_data_values:
        if attr_val in skip_elems:
            continue

        if isinstance(attr_val, QuamElement):
            yield from iterate_quam_elements(attr_val, skip_elems=skip_elems)
        if isinstance(attr_val, list):
            for elem in attr_val:
                if not isinstance(elem, QuamElement):
                    continue
                if elem in skip_elems:
                    continue
                yield from iterate_quam_elements(elem, skip_elems=skip_elems)

