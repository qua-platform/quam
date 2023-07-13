from pathlib import Path

from typing import Union

from .qua_config import build_config
from quam_components.serialise import get_serialiser
from quam_components.core.quam_instantiation import instantiate_quam_base


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