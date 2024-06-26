from quam.components.channels import InSingleChannel
from quam.utils.dataclass import get_dataclass_attr_annotations


def test_in_single_channel_attr_annotations():
    attr_annotations = get_dataclass_attr_annotations(InSingleChannel)
    assert set(attr_annotations["required"]) == {"opx_input"}
    assert set(attr_annotations["optional"]) == {
        "operations",
        "id",
        "digital_outputs",
        "opx_input_offset",
        "time_of_flight",
        "smearing",
    }


def test_generate_config(qua_config):
    channel = InSingleChannel(id="input_channel", opx_input=("con1", 1))

    channel.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_inputs": {
                1: {},
            },
            "analog_outputs": {},
            "digital_outputs": {},
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
