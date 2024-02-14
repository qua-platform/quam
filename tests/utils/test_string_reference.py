import pytest
from quam.components.channels import IQChannel
from quam.utils.string_reference import *


def test_is_reference():
    assert is_reference("#/a")
    assert is_reference("#/a.b")
    assert is_reference("#/a[0]")
    assert is_reference("#./a")
    assert is_reference("#./a.b")
    assert is_reference("#./a[0]")
    assert is_reference("#../a")
    assert is_reference("#../a.b")
    assert is_reference("#../a[0]")
    assert not is_reference("#a")
    assert not is_reference("#a.b")
    assert not is_reference("#a[0]")
    assert not is_reference("a")
    assert not is_reference("a.b")
    assert not is_reference("a[0]")
    assert not is_reference(1)
    assert not is_reference(None)
    assert not is_reference("[0]")


def test_is_absolute_reference():
    assert is_absolute_reference("#/a")
    assert is_absolute_reference("#/a.b")
    assert is_absolute_reference("#/a[0]")
    assert not is_absolute_reference("#a")
    assert not is_absolute_reference("a")
    assert not is_absolute_reference("a.b")
    assert not is_absolute_reference("a[0]")
    assert not is_absolute_reference(1)
    assert not is_absolute_reference(None)
    assert not is_absolute_reference("[0]")
    assert not is_absolute_reference("#.a")
    assert not is_absolute_reference("#./a")
    assert not is_absolute_reference("#../a")


def test_split_next_attribute():
    assert split_next_attribute("#/a") == ("a", "")
    assert split_next_attribute("#/") == ("", "")
    assert split_next_attribute("#") == ("", "")
    assert split_next_attribute("/") == ("", "")
    assert split_next_attribute("") == ("", "")

    assert split_next_attribute("a") == ("a", "")
    assert split_next_attribute("a.b") == ("a.b", "")
    assert split_next_attribute("a[0]") == ("a[0]", "")
    assert split_next_attribute("a/b") == ("a", "b")
    assert split_next_attribute("/a") == ("a", "")
    assert split_next_attribute("a/") == ("a", "")
    assert split_next_attribute("a/b/c") == ("a", "b/c")


class DotDict(dict):
    """
    a dictionary that supports dot notation
    as well as dictionary access notation
    usage: d = DotDict() or d = DotDict({'val1':'first'})
    set attributes: d.val2 = 'second' or d['val2'] = 'second'
    get attributes: d.val2 or d['val2']
    """

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, "keys"):
                value = DotDict(value)
            self[key] = value

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)


def test_get_relative_reference_value():
    root = DotDict({"a": 1, "b": 2, "nested": {"a": 3, "b": 4}})

    assert get_relative_reference_value(root, "#a") == 1
    assert get_relative_reference_value(root, "#b") == 2
    with pytest.raises(AttributeError):
        get_relative_reference_value(root, "#c") is None

    assert get_relative_reference_value(root.nested, "a") == 3

    assert get_relative_reference_value(root, "#nested/a") == 3
    assert get_relative_reference_value(root, "#./nested/a") == 3
    assert get_relative_reference_value(root, "#nested/./a") == 3
    assert get_relative_reference_value(root, "#nested/a") == 3
    assert get_relative_reference_value(root, "#nested/a") == 3
    assert get_relative_reference_value(root, "#nested/././a") == 3

    with pytest.raises(AttributeError):
        assert get_relative_reference_value(root, "#nested/../a") == 1

    root.nested.parent = root
    assert get_relative_reference_value(root, "#nested/../a") == 1
    assert get_relative_reference_value(root.nested, "../a") == 1
    assert get_relative_reference_value(root.nested, "./a") == 3
    assert get_relative_reference_value(root.nested, "././a") == 3

    root.nested.nested2 = DotDict({"a": 5})
    assert get_relative_reference_value(root.nested, "./nested2/a") == 5
    assert get_relative_reference_value(root, "#./nested/nested2/a") == 5


def test_get_referenced_value():
    root = DotDict({"a": 1, "b": 2, "nested": {"a": 3, "b": 4}})
    with pytest.raises(ValueError):
        assert get_referenced_value(root, "#/a")

    assert get_referenced_value(root, "#/a", root) == 1

    assert get_referenced_value(root.nested, "#/a", root) == 1

    assert get_referenced_value(root.nested, "#./a", root) == 3

    with pytest.raises(ValueError):
        get_referenced_value(root.nested, "#./f", root)


def test_delimiter():
    from quam.examples.superconducting_qubits.components import Transmon

    transmon = Transmon(
        id=1,
        xy=IQChannel(
            opx_output_I=None,
            opx_output_Q=None,
            frequency_converter_up=None,
        ),
    )
    assert transmon.xy.name == "q1.xy"

    import quam

    try:
        quam.utils.string_reference.DELIMITER = "$"
        assert transmon.xy.name == "q1$xy"
    finally:
        quam.utils.string_reference.DELIMITER = "."
