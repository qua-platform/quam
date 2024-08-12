from typing import Any, Dict, List, Optional, Sequence, Mapping
import jsonpatch
from jsonpointer import resolve_pointer


class _Placeholder:
    pass


def jsonpatch_to_mapping(
    old: Mapping[str, Any],
    patch: Sequence[Mapping[str, Any]],
    use_preceding_hash: bool = True,
) -> Mapping[str, Mapping[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    for item in patch:
        op = item["op"]
        if op == "replace":
            old_value = resolve_pointer(old, item["path"])
            diff[item["path"]] = {
                "old": old_value,
                "new": item["value"],
            }
        elif op == "remove":
            old_value = resolve_pointer(old, item["path"])
            diff[item["path"]] = {
                "old": old_value,
            }
        elif op == "add":
            diff[item["path"]] = {
                "new": item["value"],
            }
        elif op == "copy":
            new_dst_value = resolve_pointer(old, item["from"])
            old_dst_value = resolve_pointer(old, item["path"], _Placeholder())
            diff[item["path"]] = {
                "new": new_dst_value,
            }
            if not isinstance(old_dst_value, _Placeholder):
                diff[item["path"]]["old"] = old_dst_value
        elif op == "move":
            old_src_value = resolve_pointer(old, item["from"])
            old_dst_value = resolve_pointer(old, item["path"], _Placeholder())
            if item["from"] not in diff:
                diff[item["from"]] = {
                    "old": old_src_value,
                }
            diff[item["path"]] = {
                "new": old_src_value,
            }
            if not isinstance(old_dst_value, _Placeholder):
                diff[item["path"]]["old"] = old_dst_value

    if use_preceding_hash:
        diff = {f"#{key}": val for key, val in diff.items()}
    return diff


def compare_dicts(old_dict, new_dict) -> Dict[str, Dict[str, Any]]:  # TODO
    json_patches = jsonpatch.make_patch(old_dict, new_dict)
    json_mapping = jsonpatch_to_mapping(old_dict, json_patches)
    return json_mapping


def value_to_str(value: Any) -> str:
    if value in [str, bool, int, float, type(None)]:
        return str(value)
    else:
        str_repr = str(value)[:40]
        if len(str_repr) == 40:
            str_repr += "..."
        return str_repr


def print_state_changes(state_changes: Dict[str, Dict[str, Any]], indent=0):
    for path, state_change in state_changes.items():
        old_value_str = value_to_str(state_change.get("old", None))
        new_value_str = value_to_str(state_change["new"])
        print(" " * indent, end="")
        print(f"{path}: {old_value_str} → {new_value_str}")


class StateTracker:
    def __init__(self, state: Optional[Dict[str, Any]] = None):
        self.last_state: Dict[str, Any] = state or {}
        self.last_state_changes: Dict[str, Dict[str, Any]] = {}

    def update_state(self, state):
        self.last_state_changes = compare_dicts(self.last_state, state)
        self.last_state = state

    def print_state_changes(self, new_state, indent=3, mode: str = "update"):
        if self.last_state_changes:
            print(f"State changes before last {mode}")
            print_state_changes(self.last_state_changes, indent=indent)
            print("")

        state_changes = compare_dicts(self.last_state, new_state)
        if state_changes:
            print(f"State changes after last {mode}")
            print_state_changes(state_changes, indent=indent)
