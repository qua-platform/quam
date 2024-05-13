from quam.components.channels import InSingleChannel
from quam.utils.dataclass import get_dataclass_attr_annotations


def test_in_single_channel_attr_annotations():
    attr_annotations = get_dataclass_attr_annotations(InSingleChannel)
    assert set(attr_annotations["required"]) == {"opx_input"}
    assert set(attr_annotations["optional"]) == {
        "operations",
        "_default_label",
        "id",
        "digital_outputs",
        "opx_input_offset",
        "time_of_flight",
        "smearing",
    }


# def test_generate_config():
