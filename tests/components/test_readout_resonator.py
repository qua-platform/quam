from quam_components.components import *


def test_readout_resonator():
    readout_resonator = ReadoutResonator(
        id=1,
        mixer=Mixer(
            id=1,
            port_I=1,
            port_Q=2,
            frequency_drive=5.1e9,
            local_oscillator=LocalOscillator(frequency=5e9),
        ),
    )

    d = readout_resonator.to_dict()
    assert d == {
        "id": 1,
        "mixer": {
            "id": 1,
            "port_I": 1,
            "port_Q": 2,
            "frequency_drive": 5100000000.0,
            "local_oscillator": {"frequency": 5000000000.0},
        },
    }
