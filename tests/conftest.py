import pytest

from quam.core import *


@pytest.fixture
def BareQuamRoot():
    @quam_dataclass
    class BareQuamRoot(QuamRoot): ...

    return BareQuamRoot


@pytest.fixture
def BareQuamComponent():
    @quam_dataclass
    class BareQuamComponent(QuamComponent): ...

    return BareQuamComponent


@pytest.fixture(scope="function", autouse=True)
def remove_quam_root():
    from quam.core import QuamBase

    QuamBase._root = None
