# Welcome to QuAM

Welcome to the documentation for QuAM (Quantum Abstraction Machine).
QuAM is a software framework that provides an abstraction layer for the [QUA programming language](https://docs.quantum-machines.co/).
Whereas QUA, and especially the QUA configuration, approaches quantum control from a generic hardware perspective, QuAM allows the user to interact with the Quantum Orchestration Platform from the physicist's perspective.
It does so by providing a framework that allows the creation of abstraction layers, such that instead of channels and waveforms, users can interact with qubits and qubit operations.

## Key Features
- Standard set of QuAM components (e.g. Mixer, IQChannel) that allow you to digitally represent your quantum setup.
- Automated generation of the QUA configuration from QuAM components
- Framework for easily extending QuAM with custom classes.  
  This allows you to build abstraction layers to manage even the most complex quantum setups.
- Saving / loading your QuAM state.