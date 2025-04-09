# QUAM: Quantum Abstract Machine

## Overview
QUAM (Quantum Abstract Machine) is an innovative software framework designed to provide an abstraction layer over the QUA programming language, facilitating a more intuitive interaction with quantum computing platforms. Aimed primarily at physicists and researchers, QUAM allows users to think and operate in terms of qubits and quantum operations rather than the underlying hardware specifics.

Explore detailed documentation and get started with QUAM here: [QUAM Documentation](https://qua-platform.github.io/quam/).

## Key Features
- **Abstraction Layer**: Simplifies quantum programming by providing higher-level abstractions for qubit operations.
- **Component-Based Structure**: Utilize modular components like Mixers and IQChannels for flexible quantum circuit design.
- **Automated Configuration**: Generate QUA configurations from QUAM setups seamlessly.
- **Extensibility**: Extend QUAM with custom classes to handle complex quantum computing scenarios.
- **State Management**: Features robust tools for saving and loading your quantum states, promoting reproducibility and consistency.

## Installation
To install QUAM, first ensure you have 3.9 ≤ Python ≤ 3.12 installed on your system.  
Then run the following command: 

```bash
pip install quam
```

## Quick Start
Here’s a basic example to get you started with QUAM:

```python
from quam.components import BasicQuam, SingleChannel, pulses
from qm import qua

# Create a root-level QUAM instance
machine = BasicQuam()

# Add a qubit connected to an OPX output channel
qubit = SingleChannel(opx_output=("con1", 1))
machine.channels["qubit"] = qubit

# Add a Gaussian pulse to the channel
qubit.operations["gaussian"] = pulses.GaussianPulse(
    length=100,  # Pulse length in ns
    amplitude=0.5,  # Peak amplitude of Gaussian pulse
    sigma=20,  # Standard deviation of Guassian pulse
)

# Play the Gaussian pulse on the channel within a QUA program
with qua.program() as prog:
    qubit.play("gaussian")

# Generate the QUA configuration from QUAM
qua_configuration = machine.generate_config()
```


## License
QUAM is released under the BSD-3 License. See the LICENSE file for more details.
