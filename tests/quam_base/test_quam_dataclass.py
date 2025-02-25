from dataclasses import dataclass, is_dataclass, fields, field
import pytest

from quam.utils.dataclass import get_dataclass_attr_annotations
from quam.core import quam_dataclass


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

    c = C(int_val=1)
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

    c = C(int_val=2)
    assert is_dataclass(c)
    assert c.int_val == 2
    assert c.int_val_optional == 42

    f = fields(c)
    assert len(f) == 2
    assert f[0].name == "int_val"
    assert f[1].name == "int_val_optional"


def test_dataclass_inheritance():
    @quam_dataclass
    class BaseClass:
        int_val: int

    @quam_dataclass
    class DerivedClass(BaseClass):
        int_val2: int

    with pytest.raises(TypeError):
        d = DerivedClass()
    with pytest.raises(TypeError):
        d = DerivedClass(42)

    d = DerivedClass(int_val=42, int_val2=43)

    f = fields(d)
    assert len(f) == 2
    assert f[0].name == "int_val"
    assert f[1].name == "int_val2"


def test_dataclass_inheritance_optional_derived():
    @quam_dataclass
    class BaseClass:
        int_val: int

    @quam_dataclass
    class DerivedClass(BaseClass):
        int_val2: int = 43

    with pytest.raises(TypeError):
        d = DerivedClass()
    with pytest.raises(TypeError):
        d = DerivedClass(int_val2=42)

    d = DerivedClass(int_val=42)

    assert d.int_val == 42
    assert d.int_val2 == 43
    f = fields(d)
    assert len(f) == 2
    assert f[0].name == "int_val"
    assert f[1].name == "int_val2"

    d = DerivedClass(int_val=42, int_val2=44)

    assert d.int_val == 42
    assert d.int_val2 == 44
    f = fields(d)
    assert len(f) == 2
    assert f[0].name == "int_val"
    assert f[1].name == "int_val2"


def test_dataclass_inheritance_optional_base():
    @quam_dataclass
    class BaseClass:
        int_val: int = 42

    @quam_dataclass
    class DerivedClass(BaseClass):
        int_val2: int
        int_val3: int = 44

    # TODO Raise error once REQUIRED is verified
    with pytest.raises(TypeError):
        d = DerivedClass()

    with pytest.raises(TypeError):
        d = DerivedClass(43)

    with pytest.raises(TypeError):
        d = DerivedClass(int_val=43)

    with pytest.raises(TypeError):
        d = DerivedClass(int_val3=43)

    d = DerivedClass(int_val=43, int_val2=45)
    assert d.int_val == 43
    assert d.int_val2 == 45
    assert d.int_val3 == 44

    d = DerivedClass(int_val=43, int_val2=45, int_val3=46)
    assert d.int_val == 43
    assert d.int_val2 == 45
    assert d.int_val3 == 46

    d = DerivedClass(int_val2=47)
    assert d.int_val == 42
    assert d.int_val2 == 47
    assert d.int_val3 == 44


def test_subsubclass_default_factory():
    """This bug was found quite late, and has been fixed.
    It only occurred with Python < 3.10.

    In this case, dataclass C has a keyword arg, and so class C2 cannot have args.
    patch_dataclass therefore gives the default REQUIRED to attr2
    Next, class C3 has the same attr but with a default_factory.
    Because it has a default_factory, it isn't included in C3.__dict__
    As a result, getattr(C3, "attr2") won't return 2, but instead REQUIRED.
    """

    @quam_dataclass
    class C:
        attr: int = 2

    @quam_dataclass
    class C2(C):
        attr2: int  # Adds REQUIRED default

    @quam_dataclass
    class C3(C2):
        attr2: int = field(default_factory=lambda: 2)

    attr_annotations = get_dataclass_attr_annotations(C3)
    assert attr_annotations == {
        "required": {},
        "optional": {"attr": int, "attr2": int},
        "allowed": {"attr": int, "attr2": int},
    }


def test_quam_dataclass_with_kw_only():
    @quam_dataclass(kw_only=True)
    class C:
        int_val: int
        int_val_optional: int = 42

    assert is_dataclass(C)
    with pytest.raises(TypeError):
        c = C()
    with pytest.raises(TypeError):
        c = C(int_val_optional=42)

    c = C(int_val=2)
    assert is_dataclass(c)
    assert c.int_val == 2
    assert c.int_val_optional == 42

    f = fields(c)
    assert len(f) == 2
    assert f[0].name == "int_val"
    assert f[1].name == "int_val_optional"


def test_quam_dataclass_optional_field():
    from quam.core import QuamComponent

    @quam_dataclass
    class RootClass(QuamComponent):
        optional_root_attr: int = None

    @quam_dataclass
    class DerivedClass(RootClass):
        pass

    from quam.utils.dataclass import get_dataclass_attr_annotations

    attr_annotations = get_dataclass_attr_annotations(DerivedClass)

    assert list(attr_annotations["required"]) == []
