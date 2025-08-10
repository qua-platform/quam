import pytest

from qm import qua
from quam.components.channels import Channel

try:
    from qm.exceptions import NoScopeFoundException
except ImportError:
    NoScopeFoundException = IndexError


def test_reset_if_phase():
    channel = Channel(id="test_channel")

    with pytest.raises(NoScopeFoundException):
        channel.reset_if_phase()

    with qua.program() as prog:
        channel.reset_if_phase()
