from typing import Any

import click
from qualibrate_config.cli.utils.content import get_config_file_content
from qualibrate_config.qulibrate_types import RawConfigType

from quam.config.models.quam import QuamConfig
from quam.config.vars import QUAM_CONFIG_KEY


class InvalidQuamConfigVersion(RuntimeError):
    """Base exception for QUAM config version issues"""
    pass


class InvalidQuamConfigVersionError(InvalidQuamConfigVersion):
    """Config version older than package supports (config too old)"""

    pass


class GreaterThanSupportedQuamConfigVersionError(InvalidQuamConfigVersion):
    """Config version newer than package supports (package too old)"""

    pass


def quam_version_validator(
    config: RawConfigType,
    skip_if_none: bool = True,
) -> None:
    if not skip_if_none and QUAM_CONFIG_KEY not in config:
        raise InvalidQuamConfigVersionError(
            "Qualibrate config has no 'quam' key"
        )
    version = config[QUAM_CONFIG_KEY].get("version")
    if version is None:
        raise InvalidQuamConfigVersionError(
            "Qualibrate config is missing 'version' field. "
            "Either upgrade the QUAM package to the latest version, or manually "
            "downgrade your configuration at ~/.qualibrate/config.toml to match "
            "your installed version."
        )
    if version < QuamConfig.version:
        raise InvalidQuamConfigVersionError(
            f"Your config version ({version}) is older than the supported "
            f"version ({QuamConfig.version}). "
            "Please run `quam migrate` to upgrade your configuration."
        )
    elif version > QuamConfig.version:
        raise GreaterThanSupportedQuamConfigVersionError(
            f"Your QUAM package (v{QuamConfig.version}) is older than your "
            f"config (v{version}). Please either upgrade the QUAM package to "
            "the latest version, or manually downgrade your configuration at "
            "~/.qualibrate/config.toml to match your installed version."
        )


def validate_state_path(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value is not None:
        return value
    config_path = ctx.params.get("config_path")
    missing = click.MissingParameter(
        f"Missing parameter: {param.name}", ctx=ctx, param=param
    )
    if config_path is None or not config_path.is_file():
        raise missing
    content, _ = get_config_file_content(config_path)
    state_path = content.get(QUAM_CONFIG_KEY, {}).get("state_path")
    if state_path is None:
        raise missing
    return state_path
