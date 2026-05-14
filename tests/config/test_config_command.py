"""Tests for the ``quam config`` Click command."""

import sys

import tomli_w
from click.testing import CliRunner

from quam.config.cli.config import config_command
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


def test_config_creates_new_file_when_missing(tmp_path):
    config_path = tmp_path / "config.toml"
    state_path = tmp_path / "state"

    runner = CliRunner()
    result = runner.invoke(
        config_command,
        [
            "--config-path", str(config_path),
            "--state-path", str(state_path),
            "--auto-accept",
        ],
    )

    assert result.exit_code == 0, result.output
    assert config_path.exists()
    loaded = _load_toml(config_path)
    assert loaded["quam"]["version"] == QuamConfig.version
    # write_config invokes the before-write callback which mkdirs state_path.
    assert state_path.is_dir()


def test_config_updates_existing_file_in_place(tmp_path):
    config_path = tmp_path / "config.toml"
    initial_state = tmp_path / "initial_state"
    new_state = tmp_path / "new_state"
    _write_toml(
        config_path,
        {
            "quam": {
                "version": QuamConfig.version,
                "state_path": str(initial_state),
                "raise_error_missing_reference": False,
                "serialization": {"include_defaults": True},
            }
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        config_command,
        [
            "--config-path", str(config_path),
            "--state-path", str(new_state),
            "--auto-accept",
        ],
    )

    assert result.exit_code == 0, result.output
    loaded = _load_toml(config_path)
    assert loaded["quam"]["state_path"] == str(new_state)


def test_config_state_path_inferred_from_existing_config(tmp_path):
    """If --state-path is omitted, the callback should read it from the existing file."""
    config_path = tmp_path / "config.toml"
    existing_state = tmp_path / "existing_state"
    _write_toml(
        config_path,
        {
            "quam": {
                "version": QuamConfig.version,
                "state_path": str(existing_state),
                "raise_error_missing_reference": False,
                "serialization": {"include_defaults": True},
            }
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        config_command,
        ["--config-path", str(config_path), "--auto-accept"],
    )

    assert result.exit_code == 0, result.output
    loaded = _load_toml(config_path)
    assert loaded["quam"]["state_path"] == str(existing_state)


def test_config_state_path_required_when_no_config_file(tmp_path):
    """Without an existing config and without --state-path, the validator
    raises ``MissingParameter`` and Click exits with code 2."""
    config_path = tmp_path / "config.toml"

    runner = CliRunner()
    result = runner.invoke(
        config_command,
        ["--config-path", str(config_path), "--auto-accept"],
    )

    assert result.exit_code != 0
    assert "state_path" in result.output.lower() or "missing" in result.output.lower()
