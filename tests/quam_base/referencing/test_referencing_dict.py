from quam.core import *
from quam.utils.string_reference import *


@quam_dataclass
class BareQuamRoot(QuamRoot):
    a: int = 4


def test_referencing_from_dict():
    quam_root = BareQuamRoot()
    quam_root.quam_dict = {}
    assert isinstance(quam_root.quam_dict, QuamDict)

    quam_root.a = 42
    quam_root.quam_dict["ref_a"] = "#/a"
    assert quam_root.quam_dict["ref_a"] == 42
    assert quam_root.quam_dict.ref_a == 42

    quam_root.quam_dict["ref_b"] = "#/b"
    assert quam_root.quam_dict["ref_b"] == "#/b"
    assert quam_root.quam_dict.ref_b == "#/b"
    quam_root.b = 43
    assert quam_root.quam_dict["ref_b"] == 43
    assert quam_root.quam_dict.ref_b == 43

    quam_root.quam_dict.ref_a_again = "#/a"
    assert quam_root.quam_dict.ref_a_again == 42

    assert list(quam_root.quam_dict.values()) == [42, 43, 42]


def test_referencing_to_dict():
    quam_root = BareQuamRoot()
    quam_root.quam_dict = {"a": 42, "b": 43}

    assert list(quam_root.quam_dict.keys()) == ["a", "b"]

    assert quam_root._get_referenced_value("#/quam_dict/a") == 42
    assert quam_root.quam_dict._get_referenced_value("#/quam_dict/a") == 42
    assert quam_root._get_referenced_value("#/quam_dict/b") == 43
    assert quam_root.quam_dict._get_referenced_value("#./b") == 43

    quam_root.quam_dict["a"] = 44
    assert quam_root.quam_dict["a"] == 44
    assert quam_root._get_referenced_value("#/quam_dict/a") == 44
    assert quam_root.quam_dict._get_referenced_value("#/quam_dict/a") == 44
    assert quam_root.quam_dict._get_referenced_value("#./a") == 44


def test_referencing_dict_int_keys():
    quam_root = BareQuamRoot()
    quam_root.quam_dict = {"1": 1, 2: 2}

    assert list(quam_root.quam_dict.keys()) == list(quam_root.quam_dict)
    assert list(quam_root.quam_dict) == ["1", 2]

    assert quam_root._get_referenced_value("#/quam_dict/1") == 1
    assert quam_root.quam_dict._get_referenced_value("#/quam_dict/1") == 1

    assert quam_root._get_referenced_value("#/quam_dict/2") == 2
    assert quam_root.quam_dict._get_referenced_value("#/quam_dict/2") == 2
