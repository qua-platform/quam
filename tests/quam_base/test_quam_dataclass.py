from dataclasses import dataclass, is_dataclass, fields
import pytest


from quam_components.core.quam_dataclass import quam_dataclass, REQUIRED


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

    d = DerivedClass(42, 43)

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

    d = DerivedClass(42)

    assert d.int_val == 42
    assert d.int_val2 == 43
    f = fields(d)
    assert len(f) == 2
    assert f[0].name == "int_val"
    assert f[1].name == "int_val2"

    d = DerivedClass(42, 44)

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

    d = DerivedClass(43, 45)
    assert d.int_val == 43
    assert d.int_val2 == 45
    assert d.int_val3 == 44

    d = DerivedClass(43, 45, 46)
    assert d.int_val == 43
    assert d.int_val2 == 45
    assert d.int_val3 == 46

    d = DerivedClass(int_val2=47)
    assert d.int_val == 42
    assert d.int_val2 == 47
    assert d.int_val3 == 44


@pytest.fixture
def dataclass_patch(scope="function"):
    import sys

    existing_dataclass = getattr(sys.modules[__name__], "dataclass", None)
    yield
    if existing_dataclass is not None:
        setattr(sys.modules[__name__], "dataclass", existing_dataclass)


def test_patch_dataclass(dataclass_patch):
    import sys

    if sys.version_info.minor < 10:
        with pytest.raises(TypeError):

            @dataclass(kw_only=True)
            class C:
                ...

        from quam_components.core.quam_dataclass import patch_dataclass

        patch_dataclass(__name__)

        @dataclass(kw_only=True)
        class C:
            ...


def test_dataclass_patch_teardown(dataclass_patch):
    import sys

    if sys.version_info.minor < 10:
        with pytest.raises(TypeError):

            @dataclass(kw_only=True)
            class C:
                ...
