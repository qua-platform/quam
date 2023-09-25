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
