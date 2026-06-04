import tomli_w


def write_toml(path, data):
    with path.open("wb") as f:
        tomli_w.dump(data, f)
