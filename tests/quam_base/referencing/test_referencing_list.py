from quam_components.core import *

from dataclasses import dataclass


@dataclass
class BareQuamRoot(QuamRoot):
    a: int = 4


def test_basic_list_reference():
    quam_root = BareQuamRoot()
    quam_root.quam_list = []
    assert isinstance(quam_root.quam_list, QuamList)

    quam_root.a = 42
    quam_root.quam_list.append(":a")
    assert quam_root.quam_list[0] == 42
