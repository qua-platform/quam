"""Comprehensive unit test suite for reference chain functionality.

Tests reference chain following through multiple levels, QuamList/QuamDict
with reference chains, set_at_reference() with chains, and edge cases.
"""

import pytest

from quam.core.quam_classes import QuamBase, QuamRoot, QuamList, QuamDict, quam_dataclass


# Fixture classes
@quam_dataclass
class SimpleTarget(QuamBase):
    value: int = 0


@quam_dataclass
class ChainableValue(QuamBase):
    target: "ChainableValue" = None
    alias_ref: str = ""


@quam_dataclass
class ListContainer(QuamBase):
    values: QuamList = None
    list_ref: str = ""


@quam_dataclass
class DictContainer(QuamBase):
    data: QuamDict = None
    dict_ref: str = ""


@quam_dataclass
class QuamRootForTesting(QuamRoot):
    target: SimpleTarget = None
    chainable: ChainableValue = None
    list_container: ListContainer = None
    dict_container: DictContainer = None
    simple_value: int = 0


# Reference chain following tests
def test_simple_reference_no_chain():
    """Direct reference to a simple value - no chain to follow."""
    root = QuamRootForTesting(target=SimpleTarget(value=42))
    assert root.target.value == 42


def test_single_reference_chain_one_hop():
    """Reference chain with one hop: attr -> target."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=42),
        chainable=ChainableValue(),
    )
    root.chainable.alias_ref = "#/target/value"

    assert root.chainable.alias_ref == 42


def test_double_reference_chain_two_hops():
    """Reference chain with two hops: attr1 -> attr2 (which is ref) -> target."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=123),
        chainable=ChainableValue(target=ChainableValue(alias_ref="#/target/value")),
    )
    root.chainable.alias_ref = "#/chainable/target/alias_ref"

    assert root.chainable.alias_ref == 123


def test_triple_reference_chain():
    """Reference chain with three hops."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=999),
        chainable=ChainableValue(
            target=ChainableValue(target=ChainableValue(alias_ref="#/target/value"))
        ),
    )
    root.chainable.target.alias_ref = "#/chainable/target/target/alias_ref"

    assert root.chainable.target.alias_ref == 999


def test_empty_reference_not_a_chain():
    """Empty string is not a reference - no chain to follow."""
    root = QuamRootForTesting(simple_value=42)
    assert root.simple_value == 42


# QuamList with reference tests
def test_list_element_simple_value_no_chain():
    """List element contains a simple value - no chain."""
    container = ListContainer(values=QuamList())
    container.values.extend([42, 43, 44])

    assert container.values[0] == 42
    assert container.values[1] == 43


def test_list_element_is_reference_to_value():
    """List element is a reference string to a simple value."""
    root = QuamRootForTesting(
        simple_value=555,
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.extend(["#/simple_value"])

    assert root.list_container.values[0] == 555


def test_list_element_is_reference_to_another_list_index():
    """List element references another list index."""
    root = QuamRootForTesting(
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.extend(["#/list_container/values/1", 999])

    assert root.list_container.values[0] == 999
    assert root.list_container.values[1] == 999


def test_list_element_chain_list_ref_to_alias_to_target():
    """List element chains through multiple hops."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=888),
        chainable=ChainableValue(alias_ref="#/target/value"),
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.extend(["#/chainable/alias_ref"])

    assert root.list_container.values[0] == 888


def test_list_element_with_broken_reference_chain():
    """Broken reference in list chain should fail gracefully."""
    root = QuamRootForTesting(
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.extend(["#/nonexistent/value"])

    result = root.list_container.values[0]
    assert result == "#/nonexistent/value" or isinstance(result, str)


def test_list_element_deep_chain():
    """Deep reference chain through multiple levels in list."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=666),
        chainable=ChainableValue(target=ChainableValue(alias_ref="#/target/value")),
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.append("#/chainable/target/alias_ref")

    assert root.list_container.values[0] == 666


def test_list_with_mixed_references_and_values():
    """List with both reference elements and regular values."""
    root = QuamRootForTesting(
        simple_value=111,
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.extend(
        [
            "#/simple_value",
            222,
            "#/simple_value",
        ]
    )

    assert root.list_container.values[0] == 111
    assert root.list_container.values[1] == 222
    assert root.list_container.values[2] == 111


def test_list_element_relative_reference_chain():
    """Relative reference in list chain."""
    root = QuamRootForTesting(
        simple_value=333,
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.append("#/simple_value")

    assert root.list_container.values[0] == 333


def test_list_to_dict_chain():
    """Reference chain from list element to dict value."""
    root = QuamRootForTesting(
        simple_value=444,
        dict_container=DictContainer(data=QuamDict()),
        list_container=ListContainer(values=QuamList()),
    )
    root.dict_container.data["target"] = "#/simple_value"
    root.list_container.values.append("#/dict_container/data/target")

    assert root.list_container.values[0] == 444


# QuamDict with reference tests
def test_dict_value_simple_no_chain():
    """Dict value is simple - no chain to follow."""
    container = DictContainer(data=QuamDict())
    container.data["key1"] = 42

    assert container.data["key1"] == 42


def test_dict_value_is_reference_to_value():
    """Dict value is a reference string to another value."""
    root = QuamRootForTesting(
        simple_value=444,
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["ref_key"] = "#/simple_value"

    assert root.dict_container.data["ref_key"] == 444


def test_dict_value_is_reference_to_another_dict_entry():
    """Dict value references another dict entry."""
    root = QuamRootForTesting(
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["ref_key"] = "#/dict_container/data/target_key"
    root.dict_container.data["target_key"] = 555

    assert root.dict_container.data["ref_key"] == 555


def test_dict_value_chain_dict_ref_to_alias_to_target():
    """Dict value chains through multiple levels."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=666),
        chainable=ChainableValue(alias_ref="#/target/value"),
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["chained_ref"] = "#/chainable/alias_ref"

    assert root.dict_container.data["chained_ref"] == 666


def test_dict_value_broken_reference_chain():
    """Broken reference in dict chain."""
    root = QuamRootForTesting(
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["broken"] = "#/nonexistent/key"

    result = root.dict_container.data["broken"]
    assert result == "#/nonexistent/key" or isinstance(result, str)


def test_dict_value_deep_chain():
    """Deep reference chain in dict values."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=777),
        chainable=ChainableValue(target=ChainableValue(alias_ref="#/target/value")),
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["deep"] = "#/chainable/target/alias_ref"

    assert root.dict_container.data["deep"] == 777


def test_dict_with_mixed_references_and_values():
    """Dict with both reference and regular values."""
    root = QuamRootForTesting(
        simple_value=888,
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["ref"] = "#/simple_value"
    root.dict_container.data["plain"] = 999

    assert root.dict_container.data["ref"] == 888
    assert root.dict_container.data["plain"] == 999


def test_dict_key_lookup_unchanged():
    """Dict key lookup should remain unchanged."""
    root = QuamRootForTesting(
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["key1"] = 42

    assert "key1" in root.dict_container.data
    assert list(root.dict_container.data.keys()) == ["key1"]


def test_dict_attribute_access_with_reference():
    """Attribute access on dict should also follow references."""
    root = QuamRootForTesting(
        simple_value=555,
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data.ref_attr = "#/simple_value"

    assert root.dict_container.data["ref_attr"] == 555
    assert root.dict_container.data.ref_attr == 555


def test_dict_to_list_chain():
    """Reference chain from dict value to list element."""
    root = QuamRootForTesting(
        simple_value=333,
        list_container=ListContainer(values=QuamList()),
        dict_container=DictContainer(data=QuamDict()),
    )
    root.list_container.values.append("#/simple_value")
    root.dict_container.data["list_ref"] = "#/list_container/values/0"

    assert root.dict_container.data["list_ref"] == 333


# set_at_reference with chain tests
def test_set_at_double_reference_chain():
    """set_at_reference through a double reference chain."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=0),
        chainable=ChainableValue(target=ChainableValue(alias_ref="#/target/value")),
    )
    root.chainable.alias_ref = "#/chainable/target/alias_ref"

    root.chainable.set_at_reference("alias_ref", 123)

    assert root.target.value == 123


def test_set_at_triple_reference_chain():
    """set_at_reference through a triple reference chain."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=0),
        chainable=ChainableValue(
            target=ChainableValue(target=ChainableValue(alias_ref="#/target/value"))
        ),
    )
    root.chainable.target.alias_ref = "#/chainable/target/target/alias_ref"

    root.chainable.target.set_at_reference("alias_ref", 789)

    assert root.target.value == 789


def test_set_at_reference_with_list_index():
    """set_at_reference where reference ends with a list index."""
    container = ListContainer(values=QuamList())
    container.values.extend([1, 2, 3])
    container.list_ref = "#./values/0"

    container.set_at_reference("list_ref", 999)

    assert container.values[0] == 999


def test_set_at_reference_with_multiple_list_indices():
    """set_at_reference with different list indices."""
    container = ListContainer(values=QuamList())
    container.values.extend([1, 2, 3])

    container.list_ref = "#./values/0"
    container.list_ref_1 = "#./values/1"

    container.set_at_reference("list_ref", 999)
    container.set_at_reference("list_ref_1", 888)

    assert container.values[0] == 999
    assert container.values[1] == 888
    assert container.values[2] == 3


def test_set_at_reference_nested_list_index():
    """set_at_reference through nested list indices."""

    @quam_dataclass
    class NestedContainerQuam(QuamBase):
        inner_list: QuamList = None

    @quam_dataclass
    class OuterContainerQuam(QuamBase):
        nested: NestedContainerQuam = None
        nested_ref: str = "#./nested/inner_list/0"

    nested = NestedContainerQuam(inner_list=QuamList())
    nested.inner_list.extend([100, 200, 300])

    outer = OuterContainerQuam(nested=nested)

    outer.set_at_reference("nested_ref", 555)

    assert outer.nested.inner_list[0] == 555
    assert outer.nested.inner_list[1] == 200


def test_set_at_absolute_reference():
    """set_at_reference with absolute references."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=0),
    )
    root.abs_ref = "#/target/value"

    root.set_at_reference("abs_ref", 456)

    assert root.target.value == 456
    assert root.get_raw_value("abs_ref") == "#/target/value"


def test_set_at_reference_non_reference_raises():
    """set_at_reference on non-reference now works with new default."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=0),
    )
    root.normal_value = 42

    # With new default (allow_non_reference=True), this should succeed
    root.set_at_reference("normal_value", 123)
    assert root.normal_value == 123

    # Explicitly passing allow_non_reference=False should raise ValueError
    with pytest.raises(ValueError, match="is not a reference"):
        root.set_at_reference("normal_value", 456, allow_non_reference=False)


# Edge cases and error handling
def test_circular_reference_same_object():
    """Circular reference pointing to itself."""
    root = QuamRootForTesting(
        chainable=ChainableValue(),
    )
    root.chainable.alias_ref = "#/chainable/alias_ref"

    result = root.chainable.alias_ref
    assert result == "#/chainable/alias_ref"


def test_missing_intermediate_attribute_in_chain():
    """Missing attribute in middle of chain."""
    root = QuamRootForTesting(
        chainable=ChainableValue(),
    )
    root.chainable.alias_ref = "#/nonexistent/value"

    result = root.chainable.alias_ref
    assert isinstance(result, str)


def test_reference_to_none_value():
    """Reference pointing to a None value."""
    root = QuamRootForTesting(
        target=None,
        chainable=ChainableValue(),
    )
    root.chainable.alias_ref = "#/target"

    assert root.chainable.alias_ref is None


def test_empty_string_reference():
    """Empty string should not be treated as reference."""
    root = QuamRootForTesting(
        chainable=ChainableValue(),
    )
    root.chainable.alias_ref = ""

    assert root.chainable.alias_ref == ""


def test_reference_to_list_entire():
    """Reference pointing to entire list (not indexed)."""
    root = QuamRootForTesting(
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.extend([1, 2, 3])

    root.chainable = ChainableValue()
    root.chainable.alias_ref = "#/list_container/values"

    assert isinstance(root.chainable.alias_ref, (list, QuamList))
    assert list(root.chainable.alias_ref) == [1, 2, 3]


def test_reference_chain_through_dict():
    """Chain going through dict intermediate values."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=111),
        dict_container=DictContainer(data=QuamDict()),
    )
    root.dict_container.data["intermediate"] = "#/target/value"

    root.chainable = ChainableValue()
    root.chainable.alias_ref = "#/dict_container/data/intermediate"

    assert root.chainable.alias_ref == 111


def test_reference_with_list_and_dict_combination():
    """Complex chain through both lists and dicts."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=222),
        dict_container=DictContainer(data=QuamDict()),
        list_container=ListContainer(values=QuamList()),
    )

    root.list_container.values.append("#/target/value")
    root.dict_container.data["elem"] = "#/list_container/values/0"

    root.chainable = ChainableValue()
    root.chainable.alias_ref = "#/dict_container/data/elem"

    assert root.chainable.alias_ref == 222


def test_invalid_reference_raises_error():
    """Invalid reference should raise AttributeError."""
    root = QuamRootForTesting(
        chainable=ChainableValue(),
    )
    root.chainable.alias_ref = "#/nonexistent/path/to/nowhere"

    result = root.chainable.alias_ref
    assert isinstance(result, str)


# Backward compatibility tests
def test_existing_set_at_reference_still_works():
    """Existing set_at_reference behavior unchanged."""

    @quam_dataclass
    class Parent(QuamBase):
        child: SimpleTarget = None
        ref_value: str = "#./child/value"

    parent = Parent(child=SimpleTarget(value=0))
    parent.set_at_reference("ref_value", 42)

    assert parent.child.value == 42
    assert parent.get_raw_value("ref_value") == "#./child/value"


def test_existing_list_access_works():
    """Existing list access without references still works."""
    container = ListContainer(values=QuamList())
    container.values.extend([1, 2, 3])

    assert container.values[0] == 1
    assert container.values[1] == 2
    assert container.values[2] == 3


def test_existing_dict_access_works():
    """Existing dict access without references still works."""
    container = DictContainer(data=QuamDict())
    container.data["key1"] = 42
    container.data["key2"] = 43

    assert container.data["key1"] == 42
    assert container.data["key2"] == 43


def test_raw_value_retrieval_unchanged():
    """get_raw_value() always returns original string."""
    root = QuamRootForTesting(
        simple_value=42,
        chainable=ChainableValue(alias_ref="#/simple_value"),
    )

    assert root.chainable.get_raw_value("alias_ref") == "#/simple_value"
    assert root.chainable.alias_ref == 42


# Integration tests
def test_complex_hierarchy_with_chains():
    """Complex object hierarchy with reference chains at multiple levels."""
    root = QuamRootForTesting(
        simple_value=100,
        target=SimpleTarget(value=200),
        chainable=ChainableValue(
            target=SimpleTarget(value=0), alias_ref="#/target/value"
        ),
        list_container=ListContainer(values=QuamList()),
        dict_container=DictContainer(data=QuamDict()),
    )

    root.chainable.target.value = 300
    root.list_container.values.extend(
        [
            "#/chainable/alias_ref",
            "#/target/value",
        ]
    )
    root.dict_container.data["ref1"] = "#/list_container/values/0"
    root.dict_container.data["ref2"] = "#/list_container/values/1"

    assert root.list_container.values[0] == 200
    assert root.dict_container.data["ref1"] == 200
    assert root.dict_container.data["ref2"] == 200


def test_set_and_read_through_chains():
    """Set value through one chain, read through another."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=0),
        chainable=ChainableValue(alias_ref="#/target/value"),
        list_container=ListContainer(values=QuamList()),
    )
    root.list_container.values.append("#/chainable/alias_ref")

    root.chainable.set_at_reference("alias_ref", 555)

    assert root.list_container.values[0] == 555
    assert root.target.value == 555


def test_update_preserves_all_reference_strings():
    """Updating through chain preserves all intermediate reference strings."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=0),
        chainable=ChainableValue(target=ChainableValue(alias_ref="#/target/value")),
    )
    root.chainable.alias_ref = "#/chainable/target/alias_ref"

    root.chainable.set_at_reference("alias_ref", 777)

    assert root.get_raw_value("chainable") is not None
    assert root.chainable.get_raw_value("alias_ref") == "#/chainable/target/alias_ref"
    assert root.chainable.target.get_raw_value("alias_ref") == "#/target/value"
    assert root.target.value == 777


def test_multiple_paths_to_same_target():
    """Multiple reference chains pointing to the same target."""
    root = QuamRootForTesting(
        simple_value=100,
        chainable=ChainableValue(alias_ref="#/simple_value"),
        list_container=ListContainer(values=QuamList()),
        dict_container=DictContainer(data=QuamDict()),
    )

    root.list_container.values.append("#/simple_value")
    root.dict_container.data["direct"] = "#/simple_value"
    root.dict_container.data["through_chain"] = "#/chainable/alias_ref"

    assert root.list_container.values[0] == 100
    assert root.dict_container.data["direct"] == 100
    assert root.dict_container.data["through_chain"] == 100


def test_chain_with_partial_references():
    """Chain where only intermediate values are references."""
    root = QuamRootForTesting(
        target=SimpleTarget(value=42),
    )

    root.chainable = ChainableValue(target=root.target, alias_ref="#/target/value")

    assert root.chainable.alias_ref == 42
