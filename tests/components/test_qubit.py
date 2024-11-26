from quam.components import Qubit
from quam.components.channels import IQChannel
from quam.core.quam_classes import quam_dataclass


def test_qubit_name_int():
    qubit = Qubit(id=0)
    assert qubit.name == "q0"


def test_qubit_name_str():
    qubit = Qubit(id="qubit0")
    assert qubit.name == "qubit0"


@quam_dataclass
class TestQubit(Qubit):
    xy: IQChannel
    resonator: IQChannel


def test_qubit_channels():
    qubit = TestQubit(
        id=0,
        xy=IQChannel(
            id="xy",
            opx_output_I=("con1", 1),
            opx_output_Q=("con1", 2),
            frequency_converter_up=None,
        ),
        resonator=IQChannel(
            id="resonator",
            opx_output_I=("con1", 3),
            opx_output_Q=("con1", 4),
            frequency_converter_up=None,
        ),
    )
    assert qubit.channels == {"xy": qubit.xy}


def test_qubit_channels_referenced():
    qubit = TestQubit(
        id=0,
        xy=IQChannel(
            id="xy",
            opx_output_I=("con1", 1),
            opx_output_Q=("con1", 2),
            frequency_converter_up=None,
        ),
        resonator="#./xy",
    )
    assert qubit.channels == {"xy": qubit.xy, "resonator": qubit.xy}
