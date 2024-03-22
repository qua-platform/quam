from collections import UserList
import pytest

from quam.core import *


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


def test_quam_nested_list_instantiation_explicit():
    quam_list = QuamList([1, 2, QuamList([3, 4, 5])])
    assert list(quam_list) == [1, 2, [3, 4, 5]]
    assert quam_list.data == [1, 2, [3, 4, 5]]
    assert quam_list[2] == [3, 4, 5]
    assert isinstance(quam_list[2], QuamList)


def test_quam_nested_list_instantiation_implicit():
    quam_list = QuamList([1, 2, [3, 4, 5]])
    assert list(quam_list) == [1, 2, [3, 4, 5]]
    assert quam_list.data == [1, 2, [3, 4, 5]]
    assert quam_list[2] == [3, 4, 5]
    assert isinstance(quam_list[2], QuamList)


def test_list_parent(BareQuamComponent):
    quam_list = QuamList([BareQuamComponent()])
    assert quam_list[0].parent is quam_list

    quam_list.append(BareQuamComponent())
    assert quam_list[1].parent is quam_list

    quam_list.extend([BareQuamComponent(), BareQuamComponent()])
    assert quam_list[2].parent is quam_list

    quam_list[0] = BareQuamComponent()
    assert quam_list[0].parent is quam_list


def test_list_get_attrs_error():
    quam_list = QuamList()
    with pytest.raises(NotImplementedError):
        quam_list.get_attrs()


def test_list_to_dict():
    quam_list = QuamList([1, 2, 3])
    assert quam_list.to_dict() == [1, 2, 3]