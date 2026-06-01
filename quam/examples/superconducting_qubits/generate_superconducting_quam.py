from pathlib import Path
import json

from quam.components import *  # noqa: F401, F403
from quam.components.channels import IQChannel, InOutIQChannel, SingleChannel
from quam.components.hardware import FrequencyConverter, Mixer, LocalOscillator
from quam.examples.superconducting_qubits.components import Transmon, Quam
from quam.core import QuamRoot


def create_quam_superconducting_referenced(num_qubits: int) -> QuamRoot:
    """Create a QUAM with a number of qubits.

    Args:
        num_qubits (int): Number of qubits to create.

    Returns:
        QuamRoot: A QUAM with the specified number of qubits.
    """
    machine = Quam()
    machine.wiring = {
        "qubits": {
            f"q{idx}": {
                "port_I": ("con1", 3 * idx + 3),
                "port_Q": ("con1", 3 * idx + 4),
                "port_Z": ("con1", 3 * idx + 5),
            }
            for idx in range(num_qubits)
        },
        "feedline": {
            "opx_output_I": ("con1", 1),
            "opx_output_Q": ("con1", 2),
            "opx_input_I": ("con1", 1),
            "opx_input_Q": ("con1", 2),
        },
    }

    for idx in range(num_qubits):
        # Create qubit components
        transmon = Transmon(id=idx)  # type: ignore[call-arg]
        machine.qubits[transmon.name] = transmon

        transmon.xy = IQChannel(  # type: ignore[call-arg]
            opx_output_I=f"#/wiring/qubits/q{idx}/port_I",
            opx_output_Q=f"#/wiring/qubits/q{idx}/port_Q",
            frequency_converter_up=FrequencyConverter(  # type: ignore[call-arg]
                mixer=Mixer(),
                local_oscillator=LocalOscillator(power=10, frequency=6e9),  # type: ignore[call-arg]
            ),
            intermediate_frequency=100e6,
        )

        transmon.z = SingleChannel(opx_output=f"#/wiring/qubits/q{idx}/port_Z")  # type: ignore[call-arg]

        transmon.resonator = InOutIQChannel(  # type: ignore[call-arg]
            id=idx,
            opx_output_I="#/wiring/feedline/opx_output_I",
            opx_output_Q="#/wiring/feedline/opx_output_Q",
            opx_input_I="#/wiring/feedline/opx_input_I",
            opx_input_Q="#/wiring/feedline/opx_input_Q",
            frequency_converter_up=FrequencyConverter(  # type: ignore[call-arg]
                mixer=Mixer(), local_oscillator=LocalOscillator(power=10, frequency=6e9)  # type: ignore[call-arg]
            ),
        )
    return machine


if __name__ == "__main__":
    folder = Path("quam-components/quam/examples/quam_superconducting_referenced")
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})

    qua_file = folder / "qua_config.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)

    quam_loaded = Quam.load(folder / "quam")

    qua_file = folder / "qua_config2.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)
