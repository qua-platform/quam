from pathlib import Path
from typing import Optional

from qualibrate_config.models.base.config_base import BaseConfig


class QuamConfig(BaseConfig):
    version: int = 1
    state_path: Optional[Path] = None


class QuamTopLevelConfig(BaseConfig):
    quam: QuamConfig
