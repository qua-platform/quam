import pytest

from quam.core import *
from quam.core.quam_classes import ParentDescriptor


def test_parent_descriptor():
    class C:
        parent = ParentDescriptor()

    c = C()
    assert c.parent is None

    c.parent = 42
    assert c.parent == 42
    assert c.__dict__["parent"] == 42

    with pytest.raises(AttributeError):
        c.parent = 43

    c.parent = None

    assert c.parent is None
    assert "parent" not in c.__dict__

    c.parent = 43
    assert c.parent == 43
    assert c.__dict__["parent"] == 43


def test_duplicate_parent_descriptor():
    class C:
        parent = ParentDescriptor()

    c = C()
    assert c.parent is None

    c.parent = 42
    assert c.parent == 42
    assert c.__dict__["parent"] == 42

    with pytest.raises(AttributeError):
        c.parent = 43

    c.parent = 42
    assert c.parent == 42
    assert c.__dict__["parent"] == 42


def test_double_parent_descriptor():
    class C:
        parent = ParentDescriptor()

    class D:
        parent = ParentDescriptor()

    c1 = C()
    c2 = C()
    d = D()

    c1.parent = 1
    assert c2.parent is None
    assert d.parent is None

    c2.parent = 2
    assert c1.parent == 1
    assert c2.parent == 2
    assert d.parent is None


@pytest.mark.parametrize("cls", [QuamBase, QuamRoot, QuamComponent, QuamDict, QuamList])
def test_parent_quam_class(cls):
    @quam_dataclass
    class C(cls): ...

    assert isinstance(C.parent, ParentDescriptor)
    c = C()
    assert c.parent is None

    c.parent = 42
    assert c.parent == 42


@pytest.mark.parametrize("child_cls", [QuamDict, QuamList])
@pytest.mark.parametrize("parent_cls", [QuamRoot, QuamComponent])
def test_quam_parent_child_dict(parent_cls, child_cls):
    @quam_dataclass
    class C(parent_cls): ...

    d = child_cls()
    assert d.parent is None

    c = C()
    c.d = d
    assert d.parent is c

    with pytest.raises(AttributeError):
        C().d = d

    c.d = d  # Shouldn't raise error


def test_dict_parent(BareQuamComponent, BareQuamRoot):
    quam_dict = QuamDict()

    quam_component = BareQuamComponent()
    assert quam_component.parent is None

    quam_dict["quam_component"] = quam_component
    assert quam_component.parent is quam_dict
    quam_dict["quam_component"] = quam_component  # Shouldn't raise error

    quam_root = BareQuamRoot()
    assert quam_root.parent is None
    quam_dict["quam_root"] = quam_root
    assert quam_root.parent is quam_dict
    quam_dict["quam_root"] = quam_root  # Shouldn't raise error

    quam_dict2 = QuamDict()
    with pytest.raises(AttributeError):
        quam_dict2["quam_component"] = quam_component
    with pytest.raises(AttributeError):
        quam_dict2["quam_root"] = quam_root


def test_list_parent(BareQuamComponent, BareQuamRoot):
    quam_list = QuamList()

    quam_component = BareQuamComponent()
    assert quam_component.parent is None

    quam_list.append(quam_component)
    assert quam_component.parent is quam_list
    quam_list.append(quam_component)  # Shouldn't raise error

    quam_root = BareQuamRoot()
    assert quam_root.parent is None
    quam_list.append(quam_root)
    assert quam_root.parent is quam_list
    quam_list.append(quam_root)  # Shouldn't raise error

    quam_list2 = QuamList()
    with pytest.raises(AttributeError):
        quam_list2.append(quam_component)
    with pytest.raises(AttributeError):
        quam_list2.append(quam_root)
