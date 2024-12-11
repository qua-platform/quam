from quam.core import QuamRoot, QuamComponent, quam_dataclass


@quam_dataclass
class BareQuamRoot(QuamRoot):
    pass


@quam_dataclass
class BareQuamComponent(QuamComponent):
    pass


def test_empty_quam_root_attrs():
    quam_root = BareQuamRoot()
    assert set(quam_root.get_attrs()) == set()
    assert not quam_root._attr_val_is_default("nonexisting_attr", 42)
    assert not quam_root._attr_val_is_default("nonexisting_attr", False)
    assert not quam_root._attr_val_is_default("nonexisting_attr", True)
    assert not quam_root._attr_val_is_default("nonexisting_attr", None)


def test_basic_quam_root_attrs():
    @quam_dataclass
    class QuamTest(QuamRoot):
        int_val: int

    quam_root = QuamTest(int_val=42)
    assert quam_root.get_attrs() == {"int_val": 42}
    assert quam_root._attr_val_is_default


def test_quam_root_component_attrs():
    @quam_dataclass
    class QuamTest(QuamRoot):
        int_val: int
        quam_elem: QuamComponent

    quam_root = QuamTest(int_val=42, quam_elem=BareQuamComponent())
    for val in [None, 42, False, True]:
        assert not quam_root._attr_val_is_default("int_val", val)
    assert quam_root.get_attrs() == {"int_val": 42, "quam_elem": quam_root.quam_elem}


def test_quam_root_default_attr():
    @quam_dataclass
    class QuamTest(QuamRoot):
        int_val: int = 42
        default_none: int = None

    quam_root = QuamTest()
    assert quam_root._attr_val_is_default("int_val", 42)
    assert not quam_root._attr_val_is_default("int_val", 43)
    assert not quam_root._attr_val_is_default("int_val", None)
    assert quam_root._attr_val_is_default("default_none", None)
    assert not quam_root._attr_val_is_default("default_none", 1)
    assert not quam_root._attr_val_is_default("default_none", False)
    assert not quam_root._attr_val_is_default("default_none", True)

    assert quam_root.get_attrs() == {"int_val": 42, "default_none": None}
    assert quam_root.get_attrs(include_defaults=False) == {}

    quam_root.int_val = 43
    assert quam_root.get_attrs() == {"int_val": 43, "default_none": None}
    assert quam_root.get_attrs(include_defaults=False) == {"int_val": 43}
    quam_root.default_none = 1
    assert quam_root.get_attrs() == {"int_val": 43, "default_none": 1}

    quam_root = QuamTest(int_val=43)
    assert quam_root.get_attrs() == {"int_val": 43, "default_none": None}
    assert quam_root.get_attrs(include_defaults=False) == {"int_val": 43}
