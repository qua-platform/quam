from pathlib import Path
from typing import Optional

from qualibrate_config.models.base.config_base import BaseConfig


class QuamConfig(BaseConfig):
    version: int = 3
    state_path: Optional[Path] = None
    raise_error_missing_reference: bool = False
    include_defaults_in_serialization: bool = True


class QuamTopLevelConfig(BaseConfig):
    quam: QuamConfig
