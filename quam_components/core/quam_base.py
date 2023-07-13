from .qua_config import build_config


class QuamBase:
    def build_config(self):
        return build_config(self)