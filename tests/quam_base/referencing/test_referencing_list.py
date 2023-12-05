from quam.core import *
from quam.utils.string_reference import *


@quam_dataclass
class BareQuamRoot(QuamRoot):
    a: int = 4


def test_referencing_from_list():
    quam_root = BareQuamRoot()
    quam_root.quam_list = []
    assert isinstance(quam_root.quam_list, QuamList)

    quam_root.a = 42
    quam_root.quam_list.append("#/a")
    assert quam_root.quam_list[0] == 42
    assert quam_root.quam_list[:] == [42]

    quam_root.quam_list.append("#/b")
    assert quam_root.quam_list[1] == "#/b"
    quam_root.b = 43
    assert quam_root.quam_list[1] == 43

    assert list(quam_root.quam_list) == [42, 43]


def test_referencing_to_list():
    quam_root = BareQuamRoot()
    quam_root.quam_list = [42, 43]

    assert quam_root._get_referenced_value("#/quam_list/1") == 43
    assert quam_root.quam_list._get_referenced_value("#/quam_list/0") == 42
    assert quam_root._get_referenced_value("#/quam_list/0") == 42
    assert quam_root.quam_list._get_referenced_value("#./1") == 43

    quam_root.quam_list[0] = 44
    assert quam_root.quam_list[0] == 44
    assert quam_root._get_referenced_value("#/quam_list/0") == 44
    assert quam_root.quam_list._get_referenced_value("#/quam_list/0") == 44
    assert quam_root.quam_list._get_referenced_value("#./0") == 44
