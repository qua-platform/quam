import pytest
from quam.components.channels import (
    SingleChannel,
    IQChannel,
    InSingleChannel,
    InOutSingleChannel,
    InOutIQChannel,
    InSingleOutIQChannel,
    InIQOutSingleChannel,
)
from quam.components.hardware import FrequencyConverter, LocalOscillator, Mixer
from quam.components.pulses import SquarePulse

from .conftest import (
    make_lf_input_port,
    make_lf_output_port,
    make_bb_input_port,
    make_bb_output_port,
)


def _freq_converter():
    return FrequencyConverter(
        mixer=Mixer(),
        local_oscillator=LocalOscillator(frequency=5e9),
    )


def _add_single_channel(machine) -> None:
    machine.channels["drive"] = SingleChannel(
        opx_output=make_lf_output_port(1),
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_iq_channel(machine) -> None:
    machine.channels["drive"] = IQChannel(
        opx_output_I=make_lf_output_port(1),
        opx_output_Q=make_lf_output_port(2),
        frequency_converter_up=_freq_converter(),
        intermediate_frequency=100e6,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_in_single_channel(machine) -> None:
    machine.channels["readout"] = InSingleChannel(
        opx_input=make_lf_input_port(1),
        time_of_flight=280,
    )


def _add_in_out_single_channel(machine) -> None:
    machine.channels["readout"] = InOutSingleChannel(
        opx_output=make_lf_output_port(1),
        opx_input=make_lf_input_port(2),
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_in_out_iq_channel(machine) -> None:
    machine.channels["readout"] = InOutIQChannel(
        opx_output_I=make_lf_output_port(1),
        opx_output_Q=make_lf_output_port(2),
        opx_input_I=make_lf_input_port(1),
        opx_input_Q=make_lf_input_port(2),
        frequency_converter_up=_freq_converter(),
        intermediate_frequency=100e6,
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_in_single_out_iq_channel(machine) -> None:
    machine.channels["readout"] = InSingleOutIQChannel(
        opx_output_I=make_lf_output_port(1),
        opx_output_Q=make_lf_output_port(2),
        opx_input=make_lf_input_port(1),
        frequency_converter_up=_freq_converter(),
        intermediate_frequency=100e6,
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_in_iq_out_single_channel(machine) -> None:
    machine.channels["readout"] = InIQOutSingleChannel(
        opx_output=make_lf_output_port(1),
        opx_input_I=make_lf_input_port(1),
        opx_input_Q=make_lf_input_port(2),
        intermediate_frequency=100e6,
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_bb_single_channel(machine) -> None:
    machine.channels["drive"] = SingleChannel(
        opx_output=make_bb_output_port(1),
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_bb_in_out_single_channel(machine) -> None:
    machine.channels["readout"] = InOutSingleChannel(
        opx_output=make_bb_output_port(1),
        opx_input=make_bb_input_port(2),
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


@pytest.mark.parametrize(
    "add_channel",
    [
        _add_single_channel,
        _add_iq_channel,
        _add_in_single_channel,
        _add_in_out_single_channel,
        _add_in_out_iq_channel,
        _add_in_single_out_iq_channel,
        _add_in_iq_out_single_channel,
        pytest.param(
            _add_bb_single_channel,
            marks=pytest.mark.xfail(
                reason=(
                    "BB-FEM support (qm-qua-sdk PR #1234) has not been released to the "
                    "QOP simulator yet; remove this xfail once the simulator accepts "
                    "a 'BB' FEM type."
                ),
                strict=False,
            ),
        ),
        pytest.param(
            _add_bb_in_out_single_channel,
            marks=pytest.mark.xfail(
                reason=(
                    "BB-FEM support (qm-qua-sdk PR #1234) has not been released to the "
                    "QOP simulator yet; remove this xfail once the simulator accepts "
                    "a 'BB' FEM type."
                ),
                strict=False,
            ),
        ),
    ],
    ids=[
        "single_channel",
        "iq_channel",
        "in_single_channel",
        "in_out_single_channel",
        "in_out_iq_channel",
        "in_single_out_iq_channel",
        "in_iq_out_single_channel",
        "bb_single_channel",
        "bb_in_out_single_channel",
    ],
)
def test_channel_config_is_valid(validate_quam_config, add_channel):
    validate_quam_config(add_channel)
