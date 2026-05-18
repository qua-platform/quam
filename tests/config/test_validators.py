"""Tests for quam.config.validators."""

from pathlib import Path
from unittest.mock import MagicMock

import click
import pytest

from quam.config.models.quam import QuamConfig
from quam.config.validators import (
    GreaterThanSupportedQuamConfigVersionError,
    InvalidQuamConfigVersion,
    InvalidQuamConfigVersionError,
    quam_version_validator,
    validate_state_path,
)


# ------------------------- quam_version_validator -------------------------


def test_quam_version_validator_accepts_current_version():
    config = {"quam": {"version": QuamConfig.version}}
    # Should not raise.
    quam_version_validator(config)


def test_quam_version_validator_missing_quam_key_skipped_by_default():
    # skip_if_none=True (default): a config without the "quam" key would raise
    # KeyError on lookup; the validator only enforces presence when skip_if_none=False.
    with pytest.raises(KeyError):
        quam_version_validator({})


def test_quam_version_validator_missing_quam_key_strict():
    with pytest.raises(InvalidQuamConfigVersionError, match="has no 'quam' key"):
        quam_version_validator({}, skip_if_none=False)


def test_quam_version_validator_missing_version_field():
    config = {"quam": {}}
    with pytest.raises(InvalidQuamConfigVersionError, match="missing 'version' field"):
        quam_version_validator(config)


def test_quam_version_validator_older_version_raises():
    config = {"quam": {"version": QuamConfig.version - 1}}
    with pytest.raises(InvalidQuamConfigVersionError, match="older than the supported"):
        quam_version_validator(config)


def test_quam_version_validator_newer_version_raises_greater_than():
    config = {"quam": {"version": QuamConfig.version + 1}}
    with pytest.raises(
        GreaterThanSupportedQuamConfigVersionError, match="older than your"
    ):
        quam_version_validator(config)


def test_quam_version_validator_exception_hierarchy():
    # Both specific errors are subclasses of the base, so callers can catch either.
    assert issubclass(InvalidQuamConfigVersionError, InvalidQuamConfigVersion)
    assert issubclass(GreaterThanSupportedQuamConfigVersionError, InvalidQuamConfigVersion)


# ------------------------- validate_state_path -------------------------


def _make_ctx(config_path):
    cmd = click.Command(name="test")
    ctx = click.Context(cmd)
    ctx.params = {"config_path": config_path}
    return ctx


def _make_param(name="state_path"):
    param = MagicMock(spec=click.Parameter)
    param.name = name
    return param


def test_validate_state_path_returns_value_when_set():
    ctx = _make_ctx(config_path=None)
    param = _make_param()
    assert validate_state_path(ctx, param, "/explicit/path") == "/explicit/path"


def test_validate_state_path_raises_when_config_path_missing():
    ctx = _make_ctx(config_path=None)
    param = _make_param()
    with pytest.raises(click.MissingParameter):
        validate_state_path(ctx, param, None)


def test_validate_state_path_raises_when_config_file_missing(tmp_path):
    ctx = _make_ctx(config_path=tmp_path / "missing.toml")
    param = _make_param()
    with pytest.raises(click.MissingParameter):
        validate_state_path(ctx, param, None)


def test_validate_state_path_reads_from_config_file(tmp_path, mocker):
    config_path = tmp_path / "config.toml"
    config_path.write_text("")  # only existence is checked
    state_path = tmp_path / "state"

    mocker.patch(
        "quam.config.validators.get_config_file_content",
        return_value=({"quam": {"state_path": str(state_path)}}, config_path),
    )

    ctx = _make_ctx(config_path=config_path)
    param = _make_param()
    assert validate_state_path(ctx, param, None) == str(state_path)


def test_validate_state_path_raises_when_state_path_absent_from_config(tmp_path, mocker):
    config_path = tmp_path / "config.toml"
    config_path.write_text("")

    mocker.patch(
        "quam.config.validators.get_config_file_content",
        return_value=({"quam": {}}, config_path),
    )

    ctx = _make_ctx(config_path=config_path)
    param = _make_param()
    with pytest.raises(click.MissingParameter):
        validate_state_path(ctx, param, None)
