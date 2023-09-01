from quam_components.core import *


def test_basic_quam_list_properties():
    quam_list = QuamList()
    isinstance(quam_list, QuamComponent)
    isinstance(quam_list, list)

    quam_list += [1, 2, 3]
    assert list(quam_list) == [1, 2, 3]

    assert quam_list.data == [1, 2, 3]

    quam_list2 = QuamList([4, 5, 6])
    assert list(quam_list2) == [4, 5, 6]
    assert quam_list2.data == [4, 5, 6]
