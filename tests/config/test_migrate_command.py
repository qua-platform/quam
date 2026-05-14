"""Tests for the ``quam migrate`` Click command."""

import sys

import tomli_w
from click.testing import CliRunner

from quam.config.cli.migrate import migrate_command
from quam.config.models.quam import QuamConfig

if sys.version_info >= (3, 11):
    import tomllib as _toml_reader
else:
    import tomli as _toml_reader


def _write_toml(path, data):
    with path.open("wb") as f:
        tomli_w.dump(data, f)


def _load_toml(path):
    with path.open("rb") as f:
        return _toml_reader.load(f)


def test_migrate_no_config_file_is_noop(tmp_path):
    runner = CliRunner()
    missing = tmp_path / "missing.toml"

    result = runner.invoke(migrate_command, ["--config-path", str(missing)])

    assert result.exit_code == 0
    assert "Nothing to migrate" in result.output


def test_migrate_already_current_version_is_noop(tmp_path):
    config_path = tmp_path / "config.toml"
    _write_toml(config_path, {"quam": {"version": QuamConfig.version}})

    runner = CliRunner()
    result = runner.invoke(migrate_command, ["--config-path", str(config_path)])

    assert result.exit_code == 0
    assert "latest config version" in result.output


def test_migrate_forwards_v1_to_current(tmp_path):
    config_path = tmp_path / "config.toml"
    _write_toml(config_path, {"quam": {"version": 1, "state_path": "/some/path"}})

    runner = CliRunner()
    result = runner.invoke(migrate_command, ["--config-path", str(config_path)])

    assert result.exit_code == 0, result.output

    # Read back and verify the upgrade landed correctly.
    migrated = _load_toml(config_path)
    assert migrated["quam"]["version"] == QuamConfig.version
    assert migrated["quam"]["state_path"] == "/some/path"
    # v1->v2 adds raise_error_missing_reference, v2->v3 adds serialization
    assert migrated["quam"]["raise_error_missing_reference"] is False
    assert migrated["quam"]["serialization"]["include_defaults"] is True


def test_migrate_explicit_target_version(tmp_path):
    config_path = tmp_path / "config.toml"
    _write_toml(config_path, {"quam": {"version": 1, "state_path": "/x"}})

    runner = CliRunner()
    result = runner.invoke(migrate_command, ["--config-path", str(config_path), "2"])

    assert result.exit_code == 0, result.output

    migrated = _load_toml(config_path)
    assert migrated["quam"]["version"] == 2
    # Did NOT continue to v3.
    assert "serialization" not in migrated["quam"]
