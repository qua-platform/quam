"""Tests for quam.config.resolvers."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from quam.config.models.quam import QuamConfig
from quam.config.resolvers import get_quam_config, get_quam_config_path
from quam.config.validators import (
    GreaterThanSupportedQuamConfigVersionError,
    InvalidQuamConfigVersionError,
)
from quam.config.vars import CONFIG_PATH_ENV_NAME


# ------------------------- get_quam_config_path -------------------------


def test_get_quam_config_path_uses_env_var(mocker, tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_PATH_ENV_NAME, str(tmp_path))
    mock_get = mocker.patch(
        "quam.config.resolvers.get_config_file", return_value=tmp_path / "config.toml"
    )

    result = get_quam_config_path()

    assert result == tmp_path / "config.toml"
    args, kwargs = mock_get.call_args
    assert args[0] == str(tmp_path)
    assert kwargs.get("raise_not_exists") is False


def test_get_quam_config_path_defaults_to_qualibrate_path(mocker, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV_NAME, raising=False)
    mock_get = mocker.patch(
        "quam.config.resolvers.get_config_file", return_value=Path("/default/path")
    )

    get_quam_config_path()

    from quam.config.resolvers import QUALIBRATE_PATH

    args, _ = mock_get.call_args
    assert args[0] == QUALIBRATE_PATH


# ------------------------- get_quam_config -------------------------


@pytest.fixture(autouse=True)
def _disable_outer_mock_quam_config(request):
    """The outer ``mock_quam_config`` autouse fixture patches ``get_quam_config``
    itself; we want to test the real implementation. Stop those patches for this
    module only."""
    mocks = request.getfixturevalue("mock_quam_config")
    for mock in mocks:
        mock.stop() if hasattr(mock, "stop") else None
    # The fixture returns a list of mocks; patches are tracked in conftest and
    # restored at teardown. Nothing else to do here.
    yield


def _make_model(quam_cfg):
    model = MagicMock()
    model.quam = quam_cfg
    return model


def test_get_quam_config_resolves_path_when_none_given(mocker, tmp_path):
    config_path = tmp_path / "config.toml"
    quam_cfg = QuamConfig({})

    mock_path = mocker.patch(
        "quam.config.resolvers.get_quam_config_path", return_value=config_path
    )
    mocker.patch(
        "quam.config.resolvers.get_config_model", return_value=_make_model(quam_cfg)
    )

    result = get_quam_config()

    mock_path.assert_called_once()
    assert result is quam_cfg


def test_get_quam_config_returns_model_quam(mocker, tmp_path):
    quam_cfg = QuamConfig({"version": QuamConfig.version})
    mocker.patch(
        "quam.config.resolvers.get_config_model", return_value=_make_model(quam_cfg)
    )

    result = get_quam_config(config_path=tmp_path / "x.toml")
    assert result is quam_cfg


def test_get_quam_config_reraises_greater_version_without_migration(mocker, tmp_path):
    mocker.patch(
        "quam.config.resolvers.get_config_model",
        side_effect=GreaterThanSupportedQuamConfigVersionError("too new"),
    )
    migrate = mocker.patch("quam.config.resolvers.migrate_command")

    with pytest.raises(GreaterThanSupportedQuamConfigVersionError):
        get_quam_config(config_path=tmp_path / "x.toml")

    migrate.assert_not_called()


def test_get_quam_config_invalid_version_no_auto_migrate_reraises(mocker, tmp_path):
    mocker.patch(
        "quam.config.resolvers.get_config_model",
        side_effect=InvalidQuamConfigVersionError("too old"),
    )
    migrate = mocker.patch("quam.config.resolvers.migrate_command")

    with pytest.raises(InvalidQuamConfigVersionError):
        get_quam_config(config_path=tmp_path / "x.toml", auto_migrate=False)

    migrate.assert_not_called()


def test_get_quam_config_invalid_version_auto_migrates_then_reloads(mocker, tmp_path):
    quam_cfg = QuamConfig({"version": QuamConfig.version})

    # First call raises, second call (after migration) succeeds.
    mocker.patch(
        "quam.config.resolvers.get_config_model",
        side_effect=[
            InvalidQuamConfigVersionError("too old"),
            _make_model(quam_cfg),
        ],
    )
    migrate = mocker.patch("quam.config.resolvers.migrate_command")

    result = get_quam_config(config_path=tmp_path / "x.toml")

    migrate.assert_called_once()
    assert result is quam_cfg


def test_get_quam_config_migration_failure_wraps_in_runtime_error(mocker, tmp_path):
    mocker.patch(
        "quam.config.resolvers.get_config_model",
        side_effect=InvalidQuamConfigVersionError("too old"),
    )
    mocker.patch(
        "quam.config.resolvers.migrate_command",
        side_effect=ValueError("boom"),
    )

    with pytest.raises(RuntimeError, match="Failed to automatically migrate"):
        get_quam_config(config_path=tmp_path / "x.toml")


def test_get_quam_config_wraps_runtime_error_with_remediation_hint(mocker, tmp_path):
    mocker.patch(
        "quam.config.resolvers.get_config_model", side_effect=RuntimeError("broken")
    )

    with pytest.raises(RuntimeError, match='run "quam config"'):
        get_quam_config(config_path=tmp_path / "x.toml")


def test_get_quam_config_wraps_value_error_with_remediation_hint(mocker, tmp_path):
    mocker.patch(
        "quam.config.resolvers.get_config_model", side_effect=ValueError("bad")
    )

    with pytest.raises(RuntimeError, match='"quam config"'):
        get_quam_config(config_path=tmp_path / "x.toml")
