from qualibrate_config.cli.migrations.base import MigrateBase
from qualibrate_config.qulibrate_types import RawConfigType


class Migrate(MigrateBase):
    from_version: int = 1
    to_version: int = 2

    @staticmethod
    def backward(data: RawConfigType) -> RawConfigType:
        new_quam = data.pop("quam")
        assert new_quam.get("version", 2) == Migrate.to_version
        new_quam.pop("raise_error_missing_reference")
        new_quam["version"] = Migrate.from_version
        new_data = {"quam": new_quam, **data}
        return new_data

    @staticmethod
    def forward(data: RawConfigType) -> RawConfigType:
        new_quam = data.pop("quam")
        new_quam["raise_error_missing_reference"] = False
        new_quam["version"] = Migrate.to_version
        new_data = {"quam": new_quam, **data}
        return new_data
