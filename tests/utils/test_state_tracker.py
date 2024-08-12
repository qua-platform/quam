from quam.utils.state_tracker import StateTracker


def test_empty_state_tracker(capsys):
    state_tracker = StateTracker()
    assert state_tracker.last_state == {}
    assert state_tracker.last_state_changes == {}

    new_dict = {"hi": "bye"}
    state_tracker.update_state(new_dict)

    assert state_tracker.last_state == new_dict
    assert state_tracker.last_state_changes == {"#/hi": {"new": "bye"}}
