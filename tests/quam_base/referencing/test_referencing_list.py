from quam_components.core import *

from dataclasses import dataclass


@dataclass
class BareQuamRoot(QuamRoot):
    a: int = 4


def test_basic_list_reference():
    quam_root = BareQuamRoot()
    quam_root.quam_dict = {}
    assert isinstance(quam_root.quam_dict, QuamDict)
