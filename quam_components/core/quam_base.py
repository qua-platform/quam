from pathlib import Path
from typing import Union
from dataclasses import fields, is_dataclass

from .qua_config import build_config
from quam_components.serialisers import get_serialiser
from quam_components.core.quam_instantiation import instantiate_quam_base


__all__ = ["QuamBase", "QuamElement", "iterate_quam_elements"]


class QuamBase:
    def __init__(self, filepath=None):
        self.filepath = filepath

        if self.filepath is not None:
            self.serialiser = get_serialiser(self.filepath)
            self.load()
        else:
            self.serialiser = None

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

    def get_referenced_value(self, reference: str):
        ...  # TODO: implement


class QuamElement:
    controller: str = "con1"

    _quam: QuamBase = None  # TODO does this need Initvar?

    def apply_to_config(self, config):
        ...


def iterate_quam_elements(quam: Union[QuamBase, QuamElement]):
    if not is_dataclass(quam):
        return
    for data_field in fields(quam):
        val = getattr(quam, data_field.name)
        if isinstance(val, dict):
            yield from iterate_quam_elements(val)
        elif isinstance(val, list):
            for elem in val:
                if isinstance(elem, QuamElement):
                    yield elem
                    yield from iterate_quam_elements(elem)
        elif isinstance(val, QuamElement):
            yield val
            yield from iterate_quam_elements(val)
