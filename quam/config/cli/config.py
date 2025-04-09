from copy import deepcopy
from pathlib import Path

import click
from click.exceptions import Exit

from qualibrate_config.cli.migrate import migrate_command
from qualibrate_config.cli.utils.content import (
    get_config_file_content,
    simple_write,
    write_config,
)
from qualibrate_config.validation import (
    InvalidQualibrateConfigVersion,
    qualibrate_version_validator,
)
from qualibrate_config.vars import (
    DEFAULT_CONFIG_FILENAME,
    QUALIBRATE_PATH,
)
from qualibrate_config.cli.utils.from_sources import get_config_by_args_mapping

from quam.config.models import QuamConfig, QuamTopLevelConfig
from quam.config.validators import validate_state_path
from quam.config.vars import QUAM_CONFIG_KEY

__all__ = ["config_command"]


@click.command(name="config")
@click.option(
    "--config-path",
    type=click.Path(
        exists=False,
        path_type=Path,
    ),
    default=QUALIBRATE_PATH / DEFAULT_CONFIG_FILENAME,
    show_default=True,
    help=(
        "Path to the configuration file. If the path points to a file, it will "
        "be read and the old configuration will be reused, except for the "
        "variables specified by the user. If the file does not exist, a new one"
        " will be created. If the path points to a directory, a check will be "
        "made to see if files with the default name exist."
    ),
    is_eager=True,
)
@click.option(
    "--auto-accept",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Flag responsible for whether to skip confirmation of the generated config.",
)
@click.option(
    "--state-path",
    type=click.Path(file_okay=False, resolve_path=True, path_type=Path),
    callback=validate_state_path,
    # required=True,
    help="The path to the directory where the state path should be stored to.",
)
@click.option(
    "--raise-error-missing-reference",
    type=bool,
    default=False,
    show_default=True,
    help="Flag responsible for raising error if references are missing.",
)
@click.pass_context
def config_command(
    ctx: click.Context,
    config_path: Path,
    auto_accept: bool,
    state_path: Path,
    raise_error_missing_reference: bool,
) -> None:
    common_config, config_file = get_config_file_content(config_path)
    old_config = deepcopy(common_config)
    try:
        qualibrate_version_validator(common_config, False)
    except InvalidQualibrateConfigVersion:
        if common_config:
            migrate_command(["--config-path", config_path], standalone_mode=False)
            common_config, config_file = get_config_file_content(config_path)
    quam_config = common_config.get(QUAM_CONFIG_KEY, {})
    names_mapping = {
        "state_path": "state_path",
        "raise_error_missing_reference": "raise_error_missing_reference",
    }
    quam_config = get_config_by_args_mapping(
        names_mapping,
        quam_config,
        ctx,
    )
    quam_top_l = QuamTopLevelConfig({QUAM_CONFIG_KEY: quam_config})
    try:
        write_config(
            config_file,
            common_config,
            quam_top_l.quam,
            QUAM_CONFIG_KEY,
            quam_before_write_cb,
            confirm=not auto_accept,
        )
    except Exit:
        if old_config:
            simple_write(config_file, old_config)
        raise


def quam_before_write_cb(config: QuamConfig) -> None:
    if config.state_path:
        config.state_path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    config_command(
        ["--raise-error-on-missing-references", "True"], standalone_mode=False
    )
