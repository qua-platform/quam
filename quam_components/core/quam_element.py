__all__ = ['QuamElement']


class QuamElement:
    controller: str = "con1"

    def apply_to_config(self, config):
        ...