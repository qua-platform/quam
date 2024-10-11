# Welcome to QuAM

**Empowering Quantum Innovation with Enhanced Abstraction**

Welcome to the official documentation for the Quantum Abstract Machine (QuAM), a software framework designed to enhance the user experience of quantum computing by providing an abstraction layer over the [QUA programming language](https://docs.quantum-machines.co/). QuAM allows users, particularly physicists, to interact with the Quantum Orchestration Platform more intuitively, shifting from a hardware-centric to a physicist-friendly approach.

## What is QuAM?
QuAM stands out by transforming the way quantum control is perceived and implemented. While QUA and its configurations tackle quantum control from a generic hardware perspective, QuAM introduces a higher level of abstraction. It allows you to think in terms of qubits and quantum operations rather than just channels and waveforms, aligning more closely with the thought processes of physicists.

## Why Choose QuAM?

QuAM is not just a tool but a gateway to streamlined and efficient quantum computing: 
<div class="grid" markdown>

- **Component-Based Setup:** Utilize a standard set of QuAM components like [Mixers][quam.components.hardware.Mixer] and [IQChannels][quam.components.channels.IQChannel] to digitally represent and manipulate your quantum environment.
- **Automated Configuration:** Automatically generate the necessary QUA configuration from your QuAM setup, simplifying the transition from design to deployment.
- **Extensibility:** Easily extend QuAM with [custom classes](components/custom-components.md) to accommodate complex quantum setups, providing flexibility and power in your quantum computing applications.
- **State Management:** Effortlessly save and load your QuAM state, enabling consistent results and reproducibility in experiments.

```python
from quam.components import *
from qm import qua

# Create a root-level QuAM instance
machine = BasicQuAM()

# Add an OPX output channel
channel = SingleChannel(opx_output=("con1", 1))
machine.channels["output"] = channel

# Add a Gaussian pulse to the channel
channel.operations["gaussian"] = pulses.GaussianPulse(
    length=100, amplitude=0.5, sigma=20
)

# Play the Gaussian pulse within a QUA program
with qua.program() as prog:
    channel.play("gaussian")

# Generate the QUA configuration from QuAM
qua_configuration = machine.generate_config()

# Save QuAM to a JSON file
machine.save("state.json")
```
</div>


## Getting Started

- **[QuAM Installation](installation.md):** Set up QuAM on your system and get ready to explore its capabilities.
- **[QuAM Demonstration](demonstration.md):** Witness QuAM in action with practical examples and hands-on tutorials.
- **[QuAM Components](components/index.md):** Explore the core components that form the building blocks of the QuAM architecture.
- **[QuAM Features](features/index.md):** Discover the unique features and capabilities that QuAM offers for your quantum projects.
- **[QuAM Migration](migrating-to-quam.md)**: Already using QUA? Our detailed guide on migrating to QuAM are designed for a smooth transition to QuAM, letting you migrate your existing QUA projects without hassle.
- **[API References](API_references/index.md)**: Dive into the detailed API documentation to explore the classes, methods, and attributes available in QuAM.

We are thrilled to support your journey into the quantum future with QuAM. Together, let's push the boundaries of what's possible in quantum computing!
