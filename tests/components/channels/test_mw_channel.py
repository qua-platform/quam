import pytest
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


def test_mw_channel_upconverters_with_frequency():
    """Test successful access to upconverter frequency from upconverters dictionary."""
    opx_output = MWFEMAnalogOutputPort(
        controller_id="con1",
        fem_id=1,
        port_id=1,
        band=1,
        upconverters={1: {"frequency": 5e9}, 2: {"frequency": 6e9}},
    )
    channel = MWChannel(opx_output=opx_output, upconverter=1, intermediate_frequency=0)

    assert channel.upconverter_frequency == 5e9
    assert channel.LO_frequency == 5e9

    # Test with different upconverter
    channel.upconverter = 2
    assert channel.upconverter_frequency == 6e9


def test_mw_channel_missing_frequency_key():
    """Test error handling when frequency key is missing from upconverter config."""
    opx_output = MWFEMAnalogOutputPort(
        controller_id="con1",
        fem_id=1,
        port_id=1,
        band=1,
        upconverters={1: {"power": 10}},  # Missing frequency key
    )
    channel = MWChannel(opx_output=opx_output, upconverter=1, intermediate_frequency=0)

    with pytest.raises(
        ValueError, match="'frequency' key not found in upconverter 1 configuration"
    ):
        _ = channel.upconverter_frequency


def test_mw_channel_missing_upconverter():
    """Test error handling when upconverter ID is not found in upconverters dictionary."""
    opx_output = MWFEMAnalogOutputPort(
        controller_id="con1",
        fem_id=1,
        port_id=1,
        band=1,
        upconverters={1: {"frequency": 5e9}},  # Only upconverter 1 exists
    )
    channel = MWChannel(
        opx_output=opx_output, upconverter=3, intermediate_frequency=0
    )  # Request upconverter 3

    with pytest.raises(
        ValueError, match="Upconverter 3 not found in upconverters dictionary"
    ):
        _ = channel.upconverter_frequency
