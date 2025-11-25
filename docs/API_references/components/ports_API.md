# QUAM Ports API

Welcome to the QUAM Ports API Documentation.
The QUAM Ports module provides abstractions for hardware connection points including analog and digital inputs/outputs.
Information can be found in [QUAM Ports Documentation](/components/channel-ports) in the User Guide.

This section provides detailed API references for port types—from base ports to specific analog and digital implementations—that represent physical connections between the quantum control hardware and quantum devices.

::: quam.components.ports
    options:
      members:
        - BasePort
        - OPXPlusPort
        - FEMPort
        - OPXPlusAnalogOutputPort
        - OPXPlusAnalogInputPort
        - LFAnalogOutputPort
        - LFAnalogInputPort
        - LFFEMAnalogOutputPort
        - LFFEMAnalogInputPort
        - MWFEMAnalogOutputPort
        - MWFEMAnalogInputPort
        - OPXPlusDigitalOutputPort
        - OPXPlusDigitalInputPort
        - DigitalOutputPort
        - FEMDigitalOutputPort
        - OPXPlusPortsContainer
        - FEMPortsContainer
