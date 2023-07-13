from pathlib import Path

from .qua_config import build_config
from quam_components.serialise import get_serialiser


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

        self.instantiate_contents(contents)

    def instantiate_contents(self, contents: dict):
        for key, val in contents.items():
            ...


    def build_config(self):
        return build_config(self)