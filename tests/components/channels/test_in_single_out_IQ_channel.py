from quam.components.channels import InSingleOutIQChannel
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
        "intermediate_frequency",
        "opx_output_offset_I",
        "opx_output_offset_Q",
        "id",
        "digital_outputs",
        "opx_input_offset",
        "time_of_flight",
        "smearing",
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
                1: {},
            },
            "analog_outputs": {1: {}, 2: {}},
            "digital_outputs": {},
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
