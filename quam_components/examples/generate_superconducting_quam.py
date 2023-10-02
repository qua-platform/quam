from pathlib import Path
import json

from quam_components.components import *
from quam_components.core import QuamRoot


def create_quam_superconducting_simple(num_qubits: int) -> QuamRoot:
    """Create a QuAM with a number of qubits.

    Args:
        num_qubits (int): Number of qubits to create.

    Returns:
        QuamRoot: A QuAM with the specified number of qubits.
    """
    quam = QuAM()

    for idx in range(num_qubits):
        # Create qubit components
        local_oscillator_qubit = LocalOscillator(
            id=f"lo_q{idx}", power=10, frequency=6e9
        )
        quam.local_oscillators.append(local_oscillator_qubit)

        mixer_qubit = Mixer(
            id=f"mixer_q{idx}",
            local_oscillator=local_oscillator_qubit,
            port_I=1,
            port_Q=2,
            intermediate_frequency=100e6,
        )
        quam.mixers.append(mixer_qubit)
        local_oscillator_qubit.mixer = mixer_qubit

        transmon = Transmon(
            id=idx,
            xy=IQChannel(mixer=mixer_qubit, local_oscillator=local_oscillator_qubit),
            z=SingleChannel(port=5),
        )
        quam.qubits.append(transmon)

        # Create resonator components
        local_oscillator_resonator = LocalOscillator(
            id=f"lo_r{idx}", power=10, frequency=6e9
        )
        quam.local_oscillators.append(local_oscillator_resonator)

        resonator_mixer = Mixer(
            id=f"mixer_r{idx}",
            local_oscillator=local_oscillator_resonator,
            port_I=3,
            port_Q=4,
            intermediate_frequency=100e6,
        )
        quam.mixers.append(resonator_mixer)
        local_oscillator_resonator.mixer = resonator_mixer

        readout_resonator = ReadoutResonator(
            id=idx, mixer=resonator_mixer, local_oscillator=local_oscillator_resonator
        )
        quam.resonators.append(readout_resonator)

    # Create analog inputs
    quam.analog_inputs.append(AnalogInput(port=1))
    quam.analog_inputs.append(AnalogInput(port=2))
    return quam


def create_quam_superconducting_referenced(num_qubits: int) -> QuamRoot:
    """Create a QuAM with a number of qubits.

    Args:
        num_qubits (int): Number of qubits to create.

    Returns:
        QuamRoot: A QuAM with the specified number of qubits.
    """
    quam = QuAM()
    quam.wiring = {
        "qubits": [
            {"port_I": 5 * k + 1, "port_Q": 5 * k + 2, "port_Z": 5 * k + 3}
            for k in range(num_qubits)
        ],
        "resonators": [
            {"port_I": 5 * k + 4, "port_Q": 5 * k + 5} for k in range(num_qubits)
        ],
    }

    for idx in range(num_qubits):
        # Create qubit components
        local_oscillator_qubit = LocalOscillator(
            id=f"lo_q{idx}", power=10, frequency=6e9
        )

        mixer_qubit = Mixer(
            id=f"mixer_q{idx}",
            port_I=f":/wiring.qubits[{idx}].port_I",
            port_Q=f":/wiring.qubits[{idx}].port_Q",
            intermediate_frequency=100e6,
        )

        transmon = Transmon(
            id=idx,
            xy=IQChannel(
                mixer=mixer_qubit,
                local_oscillator=local_oscillator_qubit,
            ),
            z=SingleChannel(port=f":/wiring.qubits[{idx}].port_Z"),
        )
        quam.qubits.append(transmon)
        quam.local_oscillators.append(f":/qubits[{idx}].xy.local_oscillator")
        quam.mixers.append(f":/qubits[{idx}].xy.mixer")

        # Create resonator components
        local_oscillator_resonator = LocalOscillator(
            id=f"lo_r{idx}", power=10, frequency=6e9
        )

        resonator_mixer = Mixer(
            id=f"mixer_r{idx}",
            port_I=f":/wiring.resonators[{idx}].port_I",
            port_Q=f":/wiring.resonators[{idx}].port_Q",
            intermediate_frequency=100e6,
        )

        readout_resonator = ReadoutResonator(
            id=idx,
            mixer=resonator_mixer,
            local_oscillator=local_oscillator_resonator,
        )
        quam.resonators.append(readout_resonator)
        quam.local_oscillators.append(f":/resonators[{idx}].xy.local_oscillator")
        quam.mixers.append(f":/resonators[{idx}].xy.mixer")

    # Create analog inputs
    quam.analog_inputs.append(AnalogInput(port=1))
    quam.analog_inputs.append(AnalogInput(port=2))
    return quam


if __name__ == "__main__":
    folder = Path(
        "quam-components/quam_components/examples/quam_superconducting_referenced"
    )
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})

    qua_file = folder / "qua_config.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)

    quam_loaded = QuAM.load(folder / "quam")

    qua_file = folder / "qua_config2.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)
