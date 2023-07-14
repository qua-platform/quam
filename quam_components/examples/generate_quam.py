from quam_components.components import *
from quam_components.core import QuamBase


def create_quam_superconducting(num_qubits: int) -> QuamBase:
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

        mixer_qubit = Mixer(id=f'mixer_q{idx}', local_oscillator=local_oscillator_qubit)
        quam.mixers.append(mixer_qubit)

        transmon = Transmon(
            id=idx, 
            xy=XYChannel(mixer=mixer_qubit, pi_amp=10e-3, pi_length=40, anharmonicity=200e6),
            z=ZChannel(),
        )
        quam.qubits.append(transmon)


        # Create resonator components
        local_oscillator_resonator = LocalOscillator(power=10, frequency=6e9)
        quam.local_oscillators.append(local_oscillator_resonator)

        resonator_mixer = Mixer(id=f'mixer_r{idx}', local_oscillator=local_oscillator_qubit)
        quam.mixers.append(resonator_mixer)

        readout_resonator = ReadoutResonator(id=idx, mixer=resonator_mixer)
        quam.resonators.append(readout_resonator)
    return quam