from dataclasses import dataclass, is_dataclass, fields
import pytest


from quam_components.core.quam_dataclass import quam_dataclass


def test_dataclass_inheritance_error():
    @dataclass
    class BaseDataClass:
        b: int = 42

    with pytest.raises(TypeError):

        @dataclass
        class DerivedNondefaultDataClass(BaseDataClass):
            c: int

    @dataclass
    class DerivedDefaultDataClass(BaseDataClass):
        c: int = 41


def test_basic_quam_dataclass():
    @quam_dataclass
    class C:
        int_val: int

    assert is_dataclass(C)

    with pytest.raises(TypeError):
        c = C()

    c = C(1)
    assert is_dataclass(c)
    assert c.int_val == 1

    f = fields(c)
    assert len(f) == 1
    assert f[0].name == "int_val"


def test_quam_dataclass_with_default():
    @quam_dataclass
    class C:
        int_val: int
        int_val_optional: int = 42

    assert is_dataclass(C)
    with pytest.raises(TypeError):
        c = C()

    c = C(2)
    assert is_dataclass(c)
    assert c.int_val == 2
    assert c.int_val_optional == 42

    f = fields(c)
    assert len(f) == 2
    assert f[0].name == "int_val"
    assert f[1].name == "int_val_optional"
