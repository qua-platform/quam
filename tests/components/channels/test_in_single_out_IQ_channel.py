from quam.components.channels import InSingleOutIQChannel
from quam.components.ports.analog_inputs import OPXPlusAnalogInputPort
from quam.components.ports.analog_outputs import OPXPlusAnalogOutputPort
from quam.utils.dataclass import get_dataclass_attr_annotations


def test_in_single_channel_attr_annotations():
    attr_annotations = get_dataclass_attr_annotations(InSingleOutIQChannel)
    assert set(attr_annotations["required"]) == {
        "opx_output_I",
        "opx_output_Q",
        "opx_input",
        "frequency_converter_up",
    }
    assert set(attr_annotations["optional"]) == {
        "operations",
        "sticky",
        "intermediate_frequency",
        "LO_frequency",
        "RF_frequency",
        "opx_output_offset_I",
        "opx_output_offset_Q",
        "id",
        "digital_outputs",
        "opx_input_offset",
        "time_of_flight",
        "smearing",
        "thread"
    }


def test_generate_config(qua_config):
    channel = InSingleOutIQChannel(
        id="in_out_channel",
        opx_input=("con1", 1),
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
    )

    channel.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_inputs": {
                1: {"gain_db": 0, "shareable": False},
            },
            "analog_outputs": {
                1: {"delay": 0, "shareable": False},
                2: {"delay": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "in_out_channel": {
            "intermediate_frequency": 0.0,
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
            },
            "operations": {},
            "outputs": {"out1": ("con1", 1)},
            "smearing": 0,
            "time_of_flight": 24,
        }
    }


def test_generate_config(qua_config):
    channel = InSingleOutIQChannel(
        id="in_out_channel",
        opx_input=OPXPlusAnalogInputPort("con1", 1),
        opx_output_I=OPXPlusAnalogOutputPort("con1", 1),
        opx_output_Q=OPXPlusAnalogOutputPort("con1", 2),
        frequency_converter_up=None,
    )

    channel.apply_to_config(qua_config)
    channel.opx_input.apply_to_config(qua_config)
    channel.opx_output_I.apply_to_config(qua_config)
    channel.opx_output_Q.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_inputs": {
                1: {"gain_db": 0, "shareable": False},
            },
            "analog_outputs": {     
                1: {"delay": 0, "shareable": False},
                2: {"delay": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "in_out_channel": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
            },
            "operations": {},
            "outputs": {"out1": ("con1", 1)},
            "smearing": 0,
            "time_of_flight": 24,
        }
    }
