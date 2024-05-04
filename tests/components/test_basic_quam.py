from copy import deepcopy
from quam.components import BasicQuAM, SingleChannel
from quam.core.qua_config_template import qua_config_template


def test_instantiate_basic_quam_empty():
    quam = BasicQuAM()
    assert quam.channels == {}
    assert quam.octaves == {}

    d = quam.to_dict()
    assert d == {
        "__class__": "quam.components.basic_quam.BasicQuAM",
    }


def test_instantiate_basic_quam_with_channel():
    quam = BasicQuAM(channels={"single": SingleChannel(opx_output=("con1", 1))})
    d = quam.to_dict()
    assert d == {
        "__class__": "quam.components.basic_quam.BasicQuAM",
        "channels": {
            "single": {
                "__class__": "quam.components.channels.SingleChannel",
                "opx_output": ("con1", 1),
            },
        },
    }


def test_generate_basic_quam_config():
    quam = BasicQuAM()
    cfg = quam.generate_config()
    expected_cfg = deepcopy(qua_config_template)
    assert cfg == expected_cfg

    quam.channels = {"single": SingleChannel(opx_output=("con1", 1))}
    cfg = quam.generate_config()

    quam.channels["single"].apply_to_config(expected_cfg)
    expected_cfg["controllers"]["con1"]["analog_outputs"][1]["offset"] = 0.0

    assert cfg == expected_cfg
