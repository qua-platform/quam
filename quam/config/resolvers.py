import logging
import os
from functools import partial
from pathlib import Path
from typing import Optional

from qualibrate_config.file import get_config_file
from qualibrate_config.qulibrate_types import RawConfigType
from qualibrate_config.resolvers import get_config_model
from qualibrate_config.vars import DEFAULT_CONFIG_FILENAME, QUALIBRATE_PATH

from quam.config.cli import migrate_command
from quam.config.models import QuamConfig, QuamTopLevelConfig
from quam.config.validators import (
    quam_version_validator,
    InvalidQuamConfigVersion,
    InvalidQuamConfigVersionError,
    GreaterThanSupportedQuamConfigVersionError,
)
from quam.config.vars import CONFIG_PATH_ENV_NAME


def get_quam_config_path() -> Path:
    """
    Retrieve the quam configuration file path. If an environment variable
    for the config path is set, it uses that; otherwise, it defaults to the
    standard Qualibrate path.
    """
    return get_config_file(
        os.environ.get(CONFIG_PATH_ENV_NAME, QUALIBRATE_PATH),
        DEFAULT_CONFIG_FILENAME,
        raise_not_exists=False,
    )


def get_quam_config(
    config_path: Optional[Path] = None,
    config: Optional[RawConfigType] = None,
    auto_migrate: bool = True,
) -> QuamConfig:
    """Retrieve the Quam configuration.

    Args:
        config_path: Path to the configuration file.
            If not provided, the default path will be used.
        config: Optional pre-loaded configuration data. If not provided, it
            will load and resolve references from the config file.
        auto_migrate: is it needed to automatically apply migrations to config

    Returns:
        An instance of QuamConfig with the loaded configuration.

    Raises:
        RuntimeError: If the configuration file cannot be read or if the
            configuration state is invalid.
    """
    if config_path is None:
        config_path = get_quam_config_path()

    get_config_model_part = partial(
        get_config_model,
        config_path,
        config_key=None,
        config_class=QuamTopLevelConfig,
        config=config,
    )
    error_msg = (
        "Quam was unable to load the config. It is recommend to run "
        '"quam config" to fix any file issues. If this problem persists, '
        f'please delete "{config_path}" and retry running '
        '"quam config"'
    )
    try:
        model = get_config_model_part(raw_config_validators=[quam_version_validator])
    except GreaterThanSupportedQuamConfigVersionError:
        # Package is too old, config is too new - don't attempt migration
        raise
    except InvalidQuamConfigVersionError:
        if not auto_migrate:
            raise
        logging.info("Automatically migrate to new quam config")
        try:
            migrate_command(["--config-path", str(config_path)], standalone_mode=False)
        except Exception as migrate_error:
            # If migration fails, provide helpful context
            error_detail = f"Migration failed: {migrate_error.__class__.__name__}: {migrate_error}"
            raise RuntimeError(
                f"Failed to automatically migrate config. {error_detail}\n"
                f"Please manually upgrade your configuration or run `quam migrate`."
            ) from migrate_error
    except (RuntimeError, ValueError) as ex:
        raise RuntimeError(error_msg) from ex
    else:
        return model.quam
    # migrated
    try:
        model = get_config_model_part()
    except (RuntimeError, ValueError) as ex:
        raise RuntimeError(error_msg) from ex
    return model.quam
