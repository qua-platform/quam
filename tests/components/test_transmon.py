from quam_components.components import *


def test_basic_transmon():
    transmon = Transmon(id=1)
    assert transmon.name == "q1"
    assert transmon.id == 1
    assert transmon.frequency is None
    assert transmon.xy is None
    assert transmon.z is None

    transmon.id = "Q1"
    assert transmon.name == "Q1"


def test_transmon_xy():
    transmon = Transmon(
        id=1,
        xy=IQChannel(
            mixer=Mixer(
                id=1,
                port_I=1,
                port_Q=2,
                frequency_drive=5e9,
                local_oscillator=LocalOscillator(),
            )
        ),
    )

    assert transmon.xy.name == "q1_xy"
    assert transmon.xy.mixer.name == "mixer1"
    assert not transmon.xy.pulses
