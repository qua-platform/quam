from collections import UserList
from quam_components.core import *


def test_quam_list_inheritance():
    quam_list = QuamList()
    assert isinstance(quam_list, QuamBase)
    assert not isinstance(quam_list, list)
    assert isinstance(quam_list, QuamList)
    assert isinstance(quam_list, UserList)


def test_quam_list_equality():
    assert QuamList() == QuamList()
    assert QuamList() != QuamList([1, 2, 3])
    assert QuamList([1, 2, 3]) == QuamList([1, 2, 3])
    assert QuamList([1, 2, 3]) != QuamList([1, 2, 3, 4])

    assert QuamList() == []
    assert QuamList() != [1, 2, 3]
    assert QuamList([1, 2, 3]) == [1, 2, 3]
    assert QuamList([1, 2, 3]) != [1, 2, 3, 4]


def test_quam_list_properties():
    quam_list = QuamList()
    assert quam_list.data == []
    assert quam_list == []

    quam_list += [1, 2, 3]
    assert list(quam_list) == [1, 2, 3]
    assert quam_list == [1, 2, 3]

    assert quam_list.data == [1, 2, 3]

    quam_list2 = QuamList([4, 5, 6])
    assert list(quam_list2) == [4, 5, 6]
    assert quam_list2.data == [4, 5, 6]
