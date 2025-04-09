import pytest
from quam.utils.string_reference import join_references


@pytest.mark.parametrize(
    "base, relative, expected",
    [
        ("#/a/b/c", "#./d/e/f", "#/a/b/c/d/e/f"),
        ("#/a/b/c", "#../d/e/f", "#/a/b/d/e/f"),
        ("#/a/b/c", "#../../d/e/f", "#/a/d/e/f"),
        ("#/a/b/c", "#./a/b/../d/e/f", "#/a/b/c/a/d/e/f"),
        ("#./a/b/c", "#./d/e/f", "#./a/b/c/d/e/f"),
        ("#./a/b/c", "#../d/e/f", "#./a/b/d/e/f"),
        ("#./a/b/c", "#../../d/e/f", "#./a/d/e/f"),
        ("#./a/b/c", "#./a/b/../d/e/f", "#./a/b/c/a/d/e/f"),
        ("#../a/b/c", "#./d/e/f", "#../a/b/c/d/e/f"),
        ("#../a/b/c", "#../d/e/f", "#../a/b/d/e/f"),
        ("#../a/b/c", "#../../d/e/f", "#../a/d/e/f"),
        ("#../a/b/c", "#./a/b/../d/e/f", "#../a/b/c/a/d/e/f"),
        ("#./a", "#../b", "#./b"),
        ("#./a", "#../../b", "#../b"),
    ],
)
def test_join_references_valid(base, relative, expected):
    assert join_references(base, relative) == expected


@pytest.mark.parametrize(
    "base, relative",
    [
        ("#/a/b/c", "#/d/e/f"),
        ("#./a/b/c", "#/d/e/f"),
        ("#../a/b/c", "#/d/e/f"),
        ("#/a", "#../../b"),
        ("#./a", "#/b"),
    ],
)
def test_join_references_invalid(base, relative):
    with pytest.raises(ValueError):
        join_references(base, relative)


def test_join_reference_from_root():
    assert join_references("#/", "#./") == "#/"
    assert join_references("#/", "#./a") == "#/a"
    with pytest.raises(ValueError):
        join_references("#/", "#../")
