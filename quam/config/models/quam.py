from pathlib import Path
from typing import Optional

from qualibrate_config.models.base.config_base import BaseConfig


class QuamConfig(BaseConfig):
    version: int = 2
    state_path: Optional[Path] = None
    raise_error_missing_reference: bool = False


class QuamTopLevelConfig(BaseConfig):
    quam: QuamConfig
