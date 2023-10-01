import pytest
from dataclasses import dataclass

from quam_components.core import *


@pytest.fixture
def BareQuamRoot():
    @dataclass
    class BareQuamRoot(QuamRoot):
        ...

    return BareQuamRoot


@pytest.fixture
def BareQuamComponent():
    @dataclass
    class BareQuamComponent(QuamComponent):
        ...

    return BareQuamComponent


@pytest.fixture(scope="function", autouse=True)
def remove_quam_root():
    from quam_components.core import QuamBase

    QuamBase._quam = None
