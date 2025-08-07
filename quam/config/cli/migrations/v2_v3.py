from qualibrate_config.cli.migrations.base import MigrateBase
from qualibrate_config.qulibrate_types import RawConfigType


class Migrate(MigrateBase):
    from_version: int = 2
    to_version: int = 3

    @staticmethod
    def backward(data: RawConfigType) -> RawConfigType:
        """
        Migrate from v3 to v2 by removing include_defaults_in_save field.
        """
        new_quam = data.pop("quam")
        assert new_quam.get("version", 3) == Migrate.to_version
        new_quam.pop("include_defaults_in_save")  # Remove the new field
        new_quam["version"] = Migrate.from_version
        new_data = {"quam": new_quam, **data}
        return new_data

    @staticmethod
    def forward(data: RawConfigType) -> RawConfigType:
        """
        Migrate from v2 to v3 by adding include_defaults_in_save = False.
        
        Setting to False preserves the existing v2 behavior where defaults 
        were excluded from saves to save space.
        """
        new_quam = data.pop("quam")
        new_quam["include_defaults_in_save"] = False  # Preserve existing behavior
        new_quam["version"] = Migrate.to_version
        new_data = {"quam": new_quam, **data}
        return new_data