from pathlib import Path
from typing import Optional

from qualibrate_config.models.base.config_base import BaseConfig


class QuamConfig(BaseConfig):
    """Configuration settings for QUAM (Quantum Abstract Machine).
    
    Attributes:
        version: Config format version number.
        state_path: Default file path for saving/loading QUAM state.
        raise_error_missing_reference: Whether to raise errors for missing references.
        include_defaults_in_save: Whether to include fields with default values when
            saving QUAM objects. When True, saved files contain complete snapshots
            including all defaults. When False, only non-default values are saved.
    """
    version: int = 3
    state_path: Optional[Path] = None
    raise_error_missing_reference: bool = False
    include_defaults_in_save: bool = True


class QuamTopLevelConfig(BaseConfig):
    quam: QuamConfig
