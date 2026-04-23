import ast
from dataclasses import field
from pathlib import Path

import pytest

from quam.core import QuamComponent, QuamRoot, quam_dataclass
from quam.core.transient import (
    MISSING,
    TransientState,
    _AttrRecord,
    _DictRecord,
    _ListRecord,
)


@quam_dataclass
class Leaf(QuamComponent):
    value: int = 0


@quam_dataclass
class Root(QuamRoot):
    child: Leaf
    mapping: dict = field(default_factory=dict)
    items: list = field(default_factory=list)


@quam_dataclass
class AttrRoot(QuamRoot):
    child: Leaf


class HookedObject:
    def __init__(self):
        object.__setattr__(self, "value", 1)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise RuntimeError("write hook should be bypassed")
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if getattr(self, "_locked", False):
            raise RuntimeError("delete hook should be bypassed")
        super().__delattr__(name)


def test_transient_state_records_first_attr_write_and_can_remove():
    root = Root(child=Leaf(value=1))
    state = TransientState()
    state._is_recording = True

    token = state.record(_AttrRecord(root.child, "value", 1), "value")
    root.child.value = 2

    duplicate_token = state.record(_AttrRecord(root.child, "value", 2), "value")
    root.child.value = 3

    assert duplicate_token == token
    assert state.describe() == [{"path": "#/child/value", "was": 1, "now": 3}]

    state.remove(token)
    assert state.describe() == []

    state.record(_AttrRecord(root.child, "value", 3), "value")
    root.child.value = 4
    assert state.describe() == [{"path": "#/child/value", "was": 3, "now": 4}]


def test_attr_record_revert_bypasses_write_hooks_and_removes_missing_attrs():
    obj = HookedObject()
    state = TransientState()
    state._is_recording = True

    state.record(_AttrRecord(obj, "value", 1), "value")
    state.record(_AttrRecord(obj, "extra", MISSING), "extra")

    object.__setattr__(obj, "value", 9)
    object.__setattr__(obj, "extra", "temp")

    state.revert()

    assert obj.value == 1
    assert not hasattr(obj, "extra")
    assert state._is_recording is False


def test_attr_record_revert_restores_original_parent_and_clears_replacement_parent():
    original = Leaf(value=1)
    replacement = Leaf(value=2)
    root = AttrRoot(child=original)
    state = TransientState()
    state._is_recording = True

    state.record(_AttrRecord(root, "child", original), "child")
    root.child = replacement

    assert original.parent is root
    assert replacement.parent is root

    state.revert()

    assert root.child is original
    assert original.parent is root
    assert replacement.parent is None


def test_dict_record_revert_restores_original_values_and_clears_added_parents():
    original = Leaf(value=1)
    replacement = Leaf(value=2)
    added = Leaf(value=3)
    root = Root(child=Leaf(), mapping={"item": original})
    state = TransientState()
    state._is_recording = True

    state.record(_DictRecord(root.mapping, "item", original), "item")
    root.mapping["item"] = replacement

    state.record(_DictRecord(root.mapping, "added", MISSING), "added")
    root.mapping["added"] = added

    assert state.describe() == [
        {"path": "#/mapping/item", "was": original, "now": replacement},
        {"path": "#/mapping/added", "was": MISSING, "now": added},
    ]

    state.revert()

    assert root.mapping["item"] is original
    assert "added" not in root.mapping.data
    assert original.parent is root.mapping
    assert replacement.parent is None
    assert added.parent is None


def test_list_record_revert_restores_snapshot_and_clears_added_parents():
    original = Leaf(value=1)
    replacement = Leaf(value=2)
    appended = Leaf(value=3)
    root = Root(child=Leaf(), items=[original])
    state = TransientState()
    state._is_recording = True

    token = state.record(_ListRecord(root.items, root.items.data[:]), "__list__")
    root.items[0] = replacement

    duplicate_token = state.record(_ListRecord(root.items, root.items.data[:]), "__list__")
    root.items.append(appended)

    assert duplicate_token == token
    assert state.describe() == [
        {"path": "#/items", "was": [original], "now": [replacement, appended]}
    ]

    state.revert()

    assert root.items.data == [original]
    assert original.parent is root.items
    assert replacement.parent is None
    assert appended.parent is None


def test_transient_state_starts_disabled_and_revert_leaves_it_disabled():
    root = Root(child=Leaf(value=1))
    state = TransientState()

    token = state.record(_AttrRecord(root.child, "value", 1), "value")
    root.child.value = 2

    assert token == (id(root.child), "value")
    assert state.describe() == []
    assert state._is_recording is False

    state._is_recording = True
    state.record(_AttrRecord(root.child, "value", 1), "value")
    root.child.value = 3

    state.revert()

    assert root.child.value == 1
    assert state._is_recording is False


def test_transient_module_has_no_top_level_quam_classes_import():
    transient_source = Path(__file__).resolve().parents[2] / "quam" / "core" / "transient.py"
    source_text = transient_source.read_text()
    module = ast.parse(source_text)

    for node in module.body:
        if isinstance(node, ast.ImportFrom):
            assert node.module != "quam.core.quam_classes"
