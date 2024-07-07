from typing import Any, Dict, List, Optional


def compare_dicts(old_dict, new_dict) -> List[dict]:  # TODO
    return []


def value_to_str(value: Any) -> str:
    if value in [str, bool, int, float, type(None)]:
        return str(value)
    else:
        str_repr = str(value)[:20]
        if len(str_repr) == 20:
            str_repr += "..."
        return str_repr


def print_state_changes(state_changes: list, indent=0):
    for state_change in state_changes:
        old_value_str = value_to_str(state_change["old"])
        new_value_str = value_to_str(state_change["new"])
        print(" " * indent, end="")
        print(f"{state_change['path']}: {old_value_str} → {new_value_str}")


class StateTracker:
    def __init__(self, state: Optional[Dict[str, Any]] = None):
        self.last_state: Dict[str, Any] = state or {}
        self.last_state_changes: list = []

    def change_state(self, state):
        self.last_state_changes = compare_dicts(self.last_state, state)
        self.last_state = state

    def print_state_changes(self, new_state, indent=2, mode: str = "state update"):
        print(f"State updates before last {mode}")
        print_state_changes(self.last_state_changes, indent=indent)
        print("")

        print(f"State updates after last {mode}")
        state_changes = compare_dicts(self.last_state, new_state)
        print_state_changes(state_changes, indent=indent)

    def clear(self):
        self.last_state = {}
        self.last_state_changes = []
