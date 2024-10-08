from quam.components.channels import MWChannel
from quam.components.ports.analog_outputs import MWFEMAnalogOutputPort


def test_mw_channel():
    opx_output = MWFEMAnalogOutputPort(
        controller_id="con1", fem_id=1, port_id=1, band=1, upconverter_frequency=1e9
    )
    channel = MWChannel(opx_output=opx_output, upconverter=1, intermediate_frequency=0)

    assert channel.LO_frequency == 1e9
    assert channel.RF_frequency == 1e9

    channel.intermediate_frequency = 100e6
    assert channel.RF_frequency == 1.1e9
