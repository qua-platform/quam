from typing import Optional, Union
from quam.utils.type_checking import type_is_optional


def test_optional_is_optional():
    assert type_is_optional(Optional[int])
    assert type_is_optional(Optional[str])
    assert not type_is_optional(Optional[Union[str, int]])
    assert not type_is_optional(Union[str, int])
    assert not type_is_optional(int)
    assert not type_is_optional(str)
