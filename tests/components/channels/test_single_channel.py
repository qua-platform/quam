import pytest

from quam.components import *


def test_single_channel_no_name():
    channel = SingleChannel(opx_output=("con1", 1))

    bare_cfg = {
        "controllers": {},
        "elements": {},
    }

    with pytest.raises(AttributeError):
        channel.apply_to_config(bare_cfg)

    channel.id = "channel"
    channel.apply_to_config(bare_cfg)
