from pathlib import Path
from typing import Optional

from qualibrate_config.models.base.config_base import BaseConfig


class SerializationConfig(BaseConfig):
    include_defaults: bool = True


class QuamConfig(BaseConfig):
    version: int = 3
    state_path: Optional[Path] = None
    raise_error_missing_reference: bool = False
    serialization: Optional[SerializationConfig] = None


class QuamTopLevelConfig(BaseConfig):
    quam: QuamConfig
