"""Validate generated configs against qm-qua's own config schema.

Unlike the plain-dict assertions in the other `test_*_fem_*_ports.py` modules,
these tests run the config through `qm-qua`'s real marshmallow-based schema
(`qm.program._qua_config_schema.load_config`), using
`QuantumMachinesManager.set_capabilities_offline()` so no QOP server or
simulator connection is required. This catches drift between quam's output
and what the installed qm-qua actually accepts.
"""

import pytest
from qm import QuantumMachinesManager
from qm.exceptions import ConfigSchemaError
from qm.program._qua_config_schema import load_config

from quam.components.basic_quam import BasicFEMQuam, BasicOPXPlusQuam, BasicQuam
from quam.components.channels import (
    SingleChannel,
    IQChannel,
    InOutSingleChannel,
    InOutMWChannel,
    DigitalOutputChannel,
)
from quam.components.hardware import FrequencyConverter, LocalOscillator, Mixer
from quam.components.pulses import SquarePulse
from quam.components.ports import (
    LFFEMAnalogOutputPort,
    LFFEMAnalogInputPort,
    MWFEMAnalogOutputPort,
    MWFEMAnalogInputPort,
    OPXPlusAnalogOutputPort,
    OPXPlusAnalogInputPort,
    FEMDigitalOutputPort,
    BBFEMAnalogOutputPort,
    BBFEMAnalogInputPort,
)

QuantumMachinesManager.set_capabilities_offline()


def _validate_config(machine: BasicQuam) -> None:
    config = machine.generate_config()
    load_config(config)


def test_lf_fem_single_channel_config_is_valid():
    machine = BasicFEMQuam()
    machine.channels["drive"] = SingleChannel(
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )
    _validate_config(machine)


def test_lf_fem_in_out_single_channel_config_is_valid():
    machine = BasicFEMQuam()
    machine.channels["readout"] = InOutSingleChannel(
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        opx_input=LFFEMAnalogInputPort("con1", 1, 1),
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )
    _validate_config(machine)


def test_lf_fem_iq_channel_with_mixer_config_is_valid():
    machine = BasicFEMQuam()
    machine.channels["drive"] = IQChannel(
        opx_output_I=LFFEMAnalogOutputPort("con1", 1, 1),
        opx_output_Q=LFFEMAnalogOutputPort("con1", 1, 2),
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(),
            local_oscillator=LocalOscillator(frequency=5e9),
        ),
        intermediate_frequency=100e6,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )
    _validate_config(machine)


def test_lf_fem_digital_output_channel_config_is_valid():
    machine = BasicFEMQuam()
    channel = SingleChannel(
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )
    channel.digital_outputs["trigger"] = DigitalOutputChannel(
        opx_output=FEMDigitalOutputPort("con1", 1, 1)
    )
    machine.channels["drive"] = channel
    _validate_config(machine)


def test_mw_fem_in_out_channel_config_is_valid():
    machine = BasicFEMQuam()
    machine.channels["drive"] = InOutMWChannel(
        opx_output=MWFEMAnalogOutputPort(
            "con1", 1, 1, band=1, upconverter_frequency=5e9
        ),
        opx_input=MWFEMAnalogInputPort(
            "con1", 1, 1, band=1, downconverter_frequency=5e9
        ),
        upconverter=1,
        intermediate_frequency=100e6,
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )
    _validate_config(machine)


def test_opx_plus_in_out_single_channel_config_is_valid():
    machine = BasicOPXPlusQuam()
    machine.channels["readout"] = InOutSingleChannel(
        opx_output=OPXPlusAnalogOutputPort("con1", 1),
        opx_input=OPXPlusAnalogInputPort("con1", 1),
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )
    _validate_config(machine)


@pytest.mark.xfail(
    raises=ConfigSchemaError,
    reason=(
        "BB-FEM support (qm-qua-sdk PR #1234) is not in the installed qm-qua "
        "release yet; remove this xfail once qm-qua >=1.5.0 (which recognizes "
        "the 'BB' FEM type) is released and the dependency pin is bumped."
    ),
    strict=False,
)
def test_bb_fem_in_out_single_channel_config_is_valid():
    machine = BasicFEMQuam()
    machine.channels["readout"] = InOutSingleChannel(
        opx_output=BBFEMAnalogOutputPort("con1", 1, 1),
        opx_input=BBFEMAnalogInputPort("con1", 1, 1),
        time_of_flight=280,
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )
    _validate_config(machine)
