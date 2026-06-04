"""Test v1 to v2 migration for raise_error_missing_reference field."""

from quam.config.cli.migrations.v1_v2 import Migrate


def test_migration_versions_are_correct():
    assert Migrate.from_version == 1
    assert Migrate.to_version == 2


def test_forward_migration_adds_raise_error_missing_reference():
    v1_config = {
        "quam": {
            "version": 1,
            "state_path": None,
        }
    }

    v2_config = Migrate.forward(v1_config)

    assert v2_config["quam"]["version"] == 2
    assert v2_config["quam"]["raise_error_missing_reference"] is False
    assert v2_config["quam"]["state_path"] is None


def test_backward_migration_removes_raise_error_missing_reference():
    v2_config = {
        "quam": {
            "version": 2,
            "state_path": None,
            "raise_error_missing_reference": True,
        }
    }

    v1_config = Migrate.backward(v2_config)

    assert v1_config["quam"]["version"] == 1
    assert "raise_error_missing_reference" not in v1_config["quam"]
    assert v1_config["quam"]["state_path"] is None


def test_forward_preserves_other_top_level_keys():
    v1_config = {
        "quam": {"version": 1, "state_path": "/x"},
        "qualibrate": {"version": 5},
    }

    v2_config = Migrate.forward(v1_config)

    assert v2_config["qualibrate"] == {"version": 5}
    assert v2_config["quam"]["state_path"] == "/x"


def test_backward_round_trip():
    original = {
        "quam": {
            "version": 1,
            "state_path": "/tmp/state",
        }
    }

    migrated = Migrate.forward({"quam": dict(original["quam"])})
    back = Migrate.backward({"quam": dict(migrated["quam"])})

    assert back["quam"] == original["quam"]
