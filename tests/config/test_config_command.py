"""Tests for the ``quam config`` Click command."""

from click.testing import CliRunner
from qualibrate_config.cli.utils.content import get_config_file_content

from quam.config.cli.config import config_command
from quam.config.models.quam import QuamConfig


def test_config_creates_new_file_when_missing(tmp_path, write_toml):
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
    loaded, _ = get_config_file_content(config_path)
    assert loaded["quam"]["version"] == QuamConfig.version
    # write_config invokes the before-write callback which mkdirs state_path.
    assert state_path.is_dir()


def test_config_updates_existing_file_in_place(tmp_path, write_toml):
    config_path = tmp_path / "config.toml"
    initial_state = tmp_path / "initial_state"
    new_state = tmp_path / "new_state"
    write_toml(
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
    loaded, _ = get_config_file_content(config_path)
    assert loaded["quam"]["state_path"] == str(new_state)


def test_config_state_path_inferred_from_existing_config(tmp_path, write_toml):
    """If --state-path is omitted, the callback should read it from the existing file."""
    config_path = tmp_path / "config.toml"
    existing_state = tmp_path / "existing_state"
    write_toml(
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
    loaded, _ = get_config_file_content(config_path)
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
