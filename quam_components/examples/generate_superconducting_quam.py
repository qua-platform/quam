from pathlib import Path
import json

from quam_components.components import *
from quam_components.core import QuamBase


def create_quam_superconducting_simple(num_qubits: int) -> QuamBase:
    """Create a QuAM with a number of qubits.

    Args:
        num_qubits (int): Number of qubits to create.

    Returns:
        QuamBase: A QuAM with the specified number of qubits.
    """
    quam = QuAM()

    for idx in range(num_qubits):
        # Create qubit components
        local_oscillator_qubit = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_qubit)

        mixer_qubit = Mixer(
            id=f"mixer_q{idx}",
            local_oscillator=local_oscillator_qubit,
            port_I=1,
            port_Q=2,
            frequency_drive=5e9,
        )
        quam.mixers.append(mixer_qubit)  # TODO fix with reference

        transmon = Transmon(
            id=idx,
            xy=XYChannel(
                mixer=mixer_qubit, pi_amp=10e-3, pi_length=40, anharmonicity=200e6
            ),
            z=ZChannel(port=5),
        )
        quam.qubits.append(transmon)

        # Create resonator components
        local_oscillator_resonator = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_resonator)

        resonator_mixer = Mixer(
            id=f"mixer_r{idx}",
            local_oscillator=local_oscillator_resonator,
            port_I=3,
            port_Q=4,
            frequency_drive=5e9,
        )
        quam.mixers.append(resonator_mixer)

        readout_resonator = ReadoutResonator(id=idx, mixer=resonator_mixer)
        quam.resonators.append(readout_resonator)
    return quam


def create_quam_superconducting_referenced(num_qubits: int) -> QuamBase:
    """Create a QuAM with a number of qubits.

    Args:
        num_qubits (int): Number of qubits to create.

    Returns:
        QuamBase: A QuAM with the specified number of qubits.
    """
    quam = QuAM()
    quam.wiring = {
        "qubits": [{"port_I": 4 * k, "port_Q": 4 * k + 1} for k in range(num_qubits)],
        "resonators": [
            {"port_I": 4 * k + 2, "port_Q": 4 * k + 3} for k in range(num_qubits)
        ],
    }

    for idx in range(num_qubits):
        # Create qubit components
        local_oscillator_qubit = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_qubit)

        mixer_qubit = Mixer(
            id=f"mixer_q{idx}",
            local_oscillator=f":local_oscillators[{idx}]",
            port_I=f":wiring.qubits[{idx}].port_I",
            port_Q=f":wiring.qubits[{idx}].port_Q",
            frequency_drive=f":qubits[{idx}].frequency_01",
        )
        quam.mixers.append(mixer_qubit)  # TODO fix with reference

        transmon = Transmon(
            id=idx,
            xy=XYChannel(
                mixer=mixer_qubit, pi_amp=10e-3, pi_length=40, anharmonicity=200e6
            ),
            z=ZChannel(port=5),
            frequency_01=6.1e9,
        )
        quam.qubits.append(transmon)

        # Create resonator components
        local_oscillator_resonator = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_resonator)

        resonator_mixer = Mixer(
            id=f"mixer_r{idx}",
            local_oscillator=f":local_oscillators[{idx}]",
            port_I=f":wiring.resonators[{idx}].port_I",
            port_Q=f":wiring.resonators[{idx}].port_Q",
            frequency_drive=f":resonators[{idx}].frequency_opt",
        )
        quam.mixers.append(resonator_mixer)

        readout_resonator = ReadoutResonator(
            id=idx, mixer=resonator_mixer, frequency_opt=5.9e9
        )
        quam.resonators.append(readout_resonator)
    return quam


if __name__ == "__main__":
    folder = Path(
        "quam-components/quam_components/examples/quam_superconducting_referenced"
    )
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})

    qua_file = folder / "qua_config.json"
    qua_config = quam.build_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)

    quam_loaded = QuAM.load(folder / "quam")
