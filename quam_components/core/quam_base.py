from pathlib import Path

from .qua_config import build_config


class QuamBase:
    def __init__(self, filepath):
        self.filepath = filepath

    def build_config(self):
        return build_config(self)