from dataclasses import dataclass
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


@pytest.mark.parametrize("cls", [QuamBase, QuamRoot, QuamComponent])
def test_quam_parent(cls):
    @dataclass
    class C(cls):
        ...

    assert isinstance(C.parent, ParentDescriptor)
    c = C()
    assert c.parent is None

    c.parent = 42
    assert c.parent == 42
