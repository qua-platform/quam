from pathlib import Path
import json

from quam.components import *
from quam.components.channels import IQChannel, InOutIQChannel, SingleChannel
from quam.components.superconducting_qubits import Transmon, QuAM
from quam.core import QuamRoot


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
            {
                "port_I": ("con1", 5 * k + 3),
                "port_Q": ("con1", 5 * k + 4),
                "port_Z": ("con1", 5 * k + 5),
            }
            for k in range(num_qubits)
        ],
        "resonator": {
            "opx_output_I": ("con1", 1),
            "opx_output_Q": ("con1", 2),
            "opx_input_I": ("con1", 1),
            "opx_input_Q": ("con1", 2),
        },
    }

    for idx in range(num_qubits):
        # Create qubit components
        transmon = Transmon(
            id=idx,
            xy=IQChannel(
                opx_output_I=f"#/wiring/qubits/{idx}/port_I",
                opx_output_Q=f"#/wiring/qubits/{idx}/port_Q",
                frequency_converter_up=FrequencyConverter(
                    mixer=Mixer(),
                    local_oscillator=LocalOscillator(power=10, frequency=6e9),
                ),
                intermediate_frequency=100e6,
            ),
            z=SingleChannel(opx_output=f"#/wiring/qubits/{idx}/port_Z"),
        )
        quam.qubits.append(transmon)
        quam.local_oscillators.append(f"#/qubits/{idx}/xy/local_oscillator")
        quam.mixers.append(f"#/qubits/{idx}/xy/mixer")

        readout_resonator = InOutIQChannel(
            id=idx,
            opx_output_I="#/wiring/resonator/opx_output_I",
            opx_output_Q="#/wiring/resonator/opx_output_Q",
            opx_input_I="#/wiring/resonator/opx_input_I",
            opx_input_Q="#/wiring/resonator/opx_input_Q",
            frequency_converter_up=FrequencyConverter(mixer=Mixer()),
            frequency_converter_down=FrequencyConverter(),
            local_oscillator=LocalOscillator(power=10, frequency=6e9),
        )
        quam.resonators.append(readout_resonator)
        quam.local_oscillators.append(f"#/resonators/{idx}/xy/local_oscillator")
        quam.mixers.append(f"#/resonators/{idx}/xy/mixer")
    return quam


if __name__ == "__main__":
    folder = Path("quam-components/quam/examples/quam_superconducting_referenced")
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
