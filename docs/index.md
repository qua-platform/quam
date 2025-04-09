# Welcome to QUAM

**Empowering Quantum Innovation with Enhanced Abstraction**

Welcome to the official documentation for the Quantum Abstract Machine (QUAM), a software framework designed to enhance the user experience of quantum computing by providing an abstraction layer over the [QUA programming language](https://docs.quantum-machines.co/). QUAM allows users, particularly physicists, to interact with the Quantum Orchestration Platform more intuitively, shifting from a hardware-centric to a physicist-friendly approach.

## What is QUAM?

QUAM stands out by transforming the way quantum control is perceived and implemented. While QUA and its configurations tackle quantum control from a generic hardware perspective, QUAM introduces a higher level of abstraction. It allows you to think in terms of qubits and quantum operations rather than just channels and waveforms, aligning more closely with the thought processes of physicists.

## Why Choose QUAM?

QUAM is not just a tool but a gateway to streamlined and efficient quantum computing:

<div class="grid" markdown>

- **Component-Based Setup:** Utilize a standard set of QUAM components like [Mixers][quam.components.hardware.Mixer] and [IQChannels][quam.components.channels.IQChannel] to digitally represent and manipulate your quantum environment.
- **Automated Configuration:** Automatically generate the necessary QUA configuration from your QUAM setup, simplifying the transition from design to deployment.
- **Extensibility:** Easily extend QUAM with [custom classes](components/custom-components.md) to accommodate complex quantum setups, providing flexibility and power in your quantum computing applications.
- **State Management:** Effortlessly save and load your QUAM state, enabling consistent results and reproducibility in experiments.

```python
from quam.components import BasicQUAM, SingleChannel, pulses
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

</div>

## Getting Started

- **[QUAM Installation](installation.md):** Set up QUAM on your system and get ready to explore its capabilities.
- **[QUAM Demonstration](demonstration.md):** Witness QUAM in action with practical examples and hands-on tutorials.
- **[QUAM Components](components/index.md):** Explore the core components that form the building blocks of the QUAM architecture.
- **[QUAM Features](features/index.md):** Discover the unique features and capabilities that QUAM offers for your quantum projects.
- **[QUAM Migration](migrating-to-quam.md)**: Already using QUA? Our detailed guide on migrating to QUAM are designed for a smooth transition to QUAM, letting you migrate your existing QUA projects without hassle.
- **[API References](API_references/index.md)**: Dive into the detailed API documentation to explore the classes, methods, and attributes available in QUAM.

We are thrilled to support your journey into the quantum future with QUAM. Together, let's push the boundaries of what's possible in quantum computing!
