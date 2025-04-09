# QUAM Components

The components section of the Quantum Abstract Machine (QUAM) documentation outlines the modular parts of the QUAM framework, each designed to enable flexible and efficient quantum programming. Below, you'll find an overview of the main components that you can utilize and extend in your quantum projects.

## Channels

Channels are fundamental building blocks in QUAM that facilitate the routing of quantum signals to various hardware components. They serve as the conduits for pulses and other quantum operations, translating abstract quantum actions into physical outcomes on a quantum processor.

- **[Channels Documentation](channels.md)**: Explore the detailed documentation on different types of channels including IQ Channels, Single Analog Output Channels, and more.

## Pulses

Pulses in QUAM are used to manipulate qubit states through precise control over their quantum properties. These are defined with specific parameters like amplitude, duration, and waveform, allowing detailed control over quantum operations.

- **[Pulses Documentation](pulses.md)**: Learn how to define and use different types of pulses such as Gaussian, Square, and DRAG pulses in your quantum circuits.

## Qubits and Qubit Pairs

Qubits in QUAM provide an abstraction for physical quantum bits, and similarly combinations of qubits are represented by QubitPairs. This structure provides a gateway to intuitive circuit-level programming with quantum systems.

- **[Qubits and Qubit Pairs Documentation](qubits-and-qubit-pairs.md)**: Learn how to define qubits and qubit pairs. This section is followed by a guide on defining gate-level operations.

## Octave

The Octave component in QUAM handles the upconversion and downconversion of frequencies, enabling high-fidelity signal processing for quantum experiments. This is particularly important for setups requiring complex signal manipulations across multiple frequency bands.

- **[Octave Documentation](octave.md)**: Discover how to integrate and configure Octave components to work seamlessly within your QUAM environment.

## Custom QUAM Components

For users looking to expand beyond the standard QUAM toolkit, custom components provide a way to introduce novel functionalities tailored to specific quantum computing needs or experimental setups.

- **[Custom QUAM Components](custom-components.md)**: Get guidance on how to develop and integrate your own custom components into the QUAM framework.
