import pytest

from qm import qua
from quam.components.channels import Channel


def test_reset_if_phase():
    channel = Channel(id="test_channel")

    with pytest.raises(IndexError):
        channel.reset_if_phase()

    with qua.program() as prog:
        channel.reset_if_phase()
