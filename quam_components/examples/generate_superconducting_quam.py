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
        local_oscillator_qubit = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_qubit)

        mixer_qubit = Mixer(
            id=f"mixer_q{idx}",
            local_oscillator=local_oscillator_qubit,
            port_I=1,
            port_Q=2,
            frequency_drive=5e9,
        )
        quam.mixers.append(mixer_qubit)

        transmon = Transmon(
            id=idx,
            xy=IQChannel(mixer=mixer_qubit),
            z=SingleChannel(port=5),
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
        local_oscillator_qubit = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_qubit)

        mixer_qubit = Mixer(
            id=f"mixer_q{idx}",
            local_oscillator=f":/local_oscillators[{idx}]",
            port_I=f":/wiring.qubits[{idx}].port_I",
            port_Q=f":/wiring.qubits[{idx}].port_Q",
            frequency_drive=f":/qubits[{idx}].frequency",
        )
        quam.mixers.append(mixer_qubit)

        transmon = Transmon(
            id=idx,
            xy=IQChannel(mixer=f":/mixers[{2*idx}]"),
            z=SingleChannel(port=f":/wiring.qubits[{idx}].port_Z"),
            frequency=6.1e9,
        )
        quam.qubits.append(transmon)

        # Create resonator components
        local_oscillator_resonator = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_resonator)

        resonator_mixer = Mixer(
            id=f"mixer_r{idx}",
            local_oscillator=f":/local_oscillators[{idx}]",
            port_I=f":/wiring.resonators[{idx}].port_I",
            port_Q=f":/wiring.resonators[{idx}].port_Q",
            frequency_drive=f":/resonators[{idx}].frequency",
        )
        quam.mixers.append(resonator_mixer)

        readout_resonator = ReadoutResonator(
            id=idx,
            mixer=f":/mixers[{2*idx+1}]",
            frequency=5.9e9,
        )
        quam.resonators.append(readout_resonator)

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
