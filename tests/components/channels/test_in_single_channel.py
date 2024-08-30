from quam.components.channels import InSingleChannel
from quam.components.ports.analog_inputs import OPXPlusAnalogInputPort
from quam.utils.dataclass import get_dataclass_attr_annotations


def test_in_single_channel_attr_annotations():
    attr_annotations = get_dataclass_attr_annotations(InSingleChannel)
    assert set(attr_annotations["required"]) == {"opx_input"}
    assert set(attr_annotations["optional"]) == {
        "intermediate_frequency",
        "operations",
        "sticky",
        "id",
        "digital_outputs",
        "opx_input_offset",
        "time_of_flight",
        "smearing",
        "thread",
    }


def test_generate_config(qua_config):
    channel = InSingleChannel(id="input_channel", opx_input=("con1", 1))

    channel.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_inputs": {
                1: {"gain_db": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "input_channel": {
            "operations": {},
            "outputs": {"out1": ("con1", 1)},
            "smearing": 0,
            "time_of_flight": 24,
        }
    }


def test_generate_config_ports(qua_config):
    channel = InSingleChannel(
        id="input_channel", opx_input=OPXPlusAnalogInputPort("con1", 1)
    )

    channel.apply_to_config(qua_config)
    channel.opx_input.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_inputs": {
                1: {"gain_db": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "input_channel": {
            "operations": {},
            "outputs": {"out1": ("con1", 1)},
            "smearing": 0,
            "time_of_flight": 24,
        }
    }
