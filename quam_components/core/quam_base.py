from pathlib import Path

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

    def load(self, filepath=None):
        if filepath is None:
            filepath = self.filepath

        contents = self.serialiser.load(filepath)

        instantiate_quam_base(self, contents)

    def build_config(self):
        return build_config(self)