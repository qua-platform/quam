import pytest
from dataclasses import dataclass

from quam.core import *


@pytest.fixture
def BareQuamRoot():
    @dataclass
    class BareQuamRoot(QuamRoot): ...

    return BareQuamRoot


@pytest.fixture
def BareQuamComponent():
    @dataclass
    class BareQuamComponent(QuamComponent): ...

    return BareQuamComponent


@pytest.fixture(scope="function", autouse=True)
def remove_quam_root():
    from quam.core import QuamBase

    QuamBase._root = None


@pytest.fixture(scope="function", autouse=True)
def autoset_string_reference_delimiter():
    from quam.utils import string_reference as sr

    sr.DELIMITER = "/"
