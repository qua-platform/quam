import tomli_w
import pytest


@pytest.fixture
def write_toml():
    def _write(path, data):
        with path.open("wb") as f:
            tomli_w.dump(data, f)

    return _write
