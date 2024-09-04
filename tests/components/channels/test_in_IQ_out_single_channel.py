from quam.components.channels import InIQOutSingleChannel
from quam.components.ports.analog_inputs import OPXPlusAnalogInputPort
from quam.components.ports.analog_outputs import OPXPlusAnalogOutputPort
from quam.utils.dataclass import get_dataclass_attr_annotations


def test_in_single_channel_attr_annotations():
    attr_annotations = get_dataclass_attr_annotations(InIQOutSingleChannel)
    assert set(attr_annotations["required"]) == {
        "opx_output",
        "opx_input_I",
        "opx_input_Q",
    }
    assert set(attr_annotations["optional"]) == {
        "sticky",
        "operations",
        "filter_fir_taps",
        "filter_iir_taps",
        "intermediate_frequency",
        "opx_output_offset",
        "id",
        "digital_outputs",
        "time_of_flight",
        "smearing",
        "input_gain",
        "opx_input_offset_I",
        "opx_input_offset_Q",
        "frequency_converter_down",
        "thread",
    }


def test_generate_config(qua_config):
    channel = InIQOutSingleChannel(
        id="in_out_channel",
        opx_output=("con1", 1),
        opx_input_I=("con1", 1),
        opx_input_Q=("con1", 2),
        frequency_converter_down=None,
    )

    channel.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_inputs": {
                1: {"gain_db": 0, "shareable": False},
                2: {"gain_db": 0, "shareable": False},
            },
            "analog_outputs": {1: {"delay": 0, "shareable": False}},
        }
    }

    assert qua_config["elements"] == {
        "in_out_channel": {
            "operations": {},
            "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
            "singleInput": {"port": ("con1", 1)},
            "smearing": 0,
            "time_of_flight": 24,
        }
    }


def test_generate_config_ports(qua_config):
    channel = InIQOutSingleChannel(
        id="in_out_channel",
        opx_output=OPXPlusAnalogOutputPort("con1", 1),
        opx_input_I=OPXPlusAnalogInputPort("con1", 1),
        opx_input_Q=OPXPlusAnalogInputPort("con1", 2),
        frequency_converter_down=None,
    )

    channel.apply_to_config(qua_config)
    channel.opx_output.apply_to_config(qua_config)
    channel.opx_input_I.apply_to_config(qua_config)
    channel.opx_input_Q.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_inputs": {
                1: {"gain_db": 0, "shareable": False},
                2: {"gain_db": 0, "shareable": False},
            },
            "analog_outputs": {1: {"delay": 0, "shareable": False}},
        }
    }

    assert qua_config["elements"] == {
        "in_out_channel": {
            "operations": {},
            "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
            "singleInput": {"port": ("con1", 1)},
            "smearing": 0,
            "time_of_flight": 24,
        }
    }
