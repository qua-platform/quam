"""
Test script for channel-ports.md documentation examples.
Tests each code snippet for execution correctness and serialization.
"""

import sys
import traceback
from typing import Dict, List, Tuple


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.serialization_passed = False
        self.serialization_error = None

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        ser_status = "PASS" if self.serialization_passed else "FAIL"
        result = f"{self.name}: {status}"
        if self.error:
            result += f"\n  Error: {self.error}"
        result += f"\n  Serialization: {ser_status}"
        if self.serialization_error:
            result += f"\n  Serialization Error: {self.serialization_error}"
        return result


def test_snippet(name: str, code: str) -> TestResult:
    """Test a code snippet and its serialization."""
    result = TestResult(name)

    # Create a clean namespace for each test
    namespace = {}

    try:
        # Execute the code snippet
        exec(code, namespace)
        result.passed = True

        # Test serialization if machine exists
        if 'machine' in namespace:
            try:
                machine = namespace['machine']
                serialized = machine.to_dict()
                result.serialization_passed = True
            except Exception as e:
                result.serialization_error = f"{type(e).__name__}: {str(e)}"
        else:
            result.serialization_error = "No 'machine' variable found in snippet"

    except Exception as e:
        result.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

    return result


def main():
    results: List[TestResult] = []

    # Test 1: Port Containers with BasicQuam setup
    print("Testing: Port Containers with BasicFEMQuam setup...")
    code1 = """
from quam.components import BasicFEMQuam
from quam.components.ports import FEMPortsContainer

# Create a QUAM instance with ports container
machine = BasicFEMQuam(ports=FEMPortsContainer())

# Create ports using the container methods
machine.ports.get_analog_output(
    "con1", 1, 2,  # controller, fem_id, port_id
    create=True,
    offset=0.15,
    sampling_rate=2e9,  # 2 GHz sampling
)

machine.ports.get_mw_output(
    "con1", 1, 1,
    create=True,
    band=1,
    upconverter_frequency=5e9,  # 5 GHz upconverter
)
"""
    results.append(test_snippet("1. Port Containers with BasicQuam setup", code1))

    # Test 2: LF-FEM Analog Output with Port References
    print("Testing: LF-FEM Analog Output with Port References...")
    code2 = """
from quam.components import BasicFEMQuam, SingleChannel
from quam.components.ports import FEMPortsContainer

# Create QUAM instance with ports
machine = BasicFEMQuam(ports=FEMPortsContainer())

# Create the port
port = machine.ports.get_analog_output(
    "con1", 1, 2,  # controller, fem_id, port_id
    create=True,
    offset=0.15,
    sampling_rate=2e9,
    output_mode="amplified",
)

# Create channel that references this port
machine.channels["drive"] = SingleChannel(
    opx_output=port.get_reference()  # Get reference from port
)
"""
    results.append(test_snippet("2. LF-FEM Analog Output with Port References", code2))

    # Test 3: MW-FEM for Microwave Control (using MWChannel)
    print("Testing: MW-FEM for Microwave Control...")
    code3 = """
from quam.components import BasicFEMQuam
from quam.components.channels import MWChannel
from quam.components.ports import FEMPortsContainer

# Create QUAM instance with ports
machine = BasicFEMQuam()
machine.ports = FEMPortsContainer()

# Create MW-FEM output port for microwave drive
mw_port = machine.ports.get_mw_output(
    "con1", 1, 1,
    create=True,
    band=1,
    upconverter_frequency=5.5e9,  # 5.5 GHz LO frequency
    sampling_rate=1e9,
)

# Create MW channel with reference to MW-FEM port
machine.channels["qubit_xy"] = MWChannel(
    opx_output=mw_port.get_reference(),
    intermediate_frequency=100e6,  # 100 MHz IF
)
"""
    results.append(test_snippet("3. MW-FEM for Microwave Control (using MWChannel)", code3))

    # Test 4: MW-FEM Readout with Linked Frequencies (using InOutMWChannel)
    print("Testing: MW-FEM Readout with Linked Frequencies...")
    code4 = """
from quam.components import BasicFEMQuam
from quam.components.channels import InOutMWChannel
from quam.components.ports import FEMPortsContainer

machine = BasicFEMQuam(ports=FEMPortsContainer())

mw_output = machine.ports.get_mw_output("con1", 1, 1, create=True, band=1, upconverter_frequency=6e9)
mw_input = machine.ports.get_mw_input(
    "con1", 1, 1, create=True, band=1,
    downconverter_frequency=mw_output.get_reference("upconverter_frequency"),
)

machine.channels["readout"] = InOutMWChannel(
    opx_output=mw_output.get_reference(),
    opx_input=mw_input.get_reference(),
)
"""
    results.append(test_snippet("4. MW-FEM Readout with Linked Frequencies", code4))

    # Test 5: OPX+ with IQ Channels
    print("Testing: OPX+ with IQ Channels...")
    code5 = """
from quam.components import BasicOPXPlusQuam, IQChannel
from quam.components.ports import OPXPlusPortsContainer
from quam.components.hardware import FrequencyConverter, LocalOscillator, Mixer

# For OPX+ systems, use OPXPlusPortsContainer
machine = BasicOPXPlusQuam(ports=OPXPlusPortsContainer())

# Create I and Q ports
port_I = machine.ports.get_analog_output("con1", 1, create=True, offset=0.1)
port_Q = machine.ports.get_analog_output("con1", 2, create=True, offset=-0.05)

# Create IQ channel with port references
machine.channels["qubit_xy"] = IQChannel(
    opx_output_I=port_I.get_reference(),
    opx_output_Q=port_Q.get_reference(),
    intermediate_frequency=100e6,
    frequency_converter_up=FrequencyConverter(
        local_oscillator=LocalOscillator(frequency=6e9, power=10),
        mixer=Mixer(),
    )
)
"""
    results.append(test_snippet("5. OPX+ with IQ Channels", code5))

    # Test 6: LF-FEM with advanced features
    print("Testing: LF-FEM with advanced features...")
    code6 = """
from quam.components import BasicFEMQuam
from quam.components.ports import FEMPortsContainer

machine = BasicFEMQuam()
machine.ports = FEMPortsContainer()

# LF-FEM analog output with advanced features
machine.ports.get_analog_output(
    "con1", 1, 2,  # controller, fem_id, port_id
    create=True,
    offset=0.15,
    sampling_rate=2e9,  # 1 GHz or 2 GHz
    output_mode="amplified",  # "direct" or "amplified"
    exponential_filter=[(10, 0.1), (20, 0.2)],  # For QOP >= 3.3.0
)
"""
    results.append(test_snippet("6. LF-FEM with advanced features", code6))

    # Test 7: MW-FEM output with upconverter
    print("Testing: MW-FEM output with upconverter...")
    code7 = """
from quam.components import BasicFEMQuam
from quam.components.ports import FEMPortsContainer

machine = BasicFEMQuam(ports=FEMPortsContainer())

# MW-FEM output with upconverter
machine.ports.get_mw_output(
    "con1", 1, 1,  # controller, fem_id, port_id
    create=True,
    band=1,  # Required: 1 or 2
    upconverter_frequency=5.5e9,  # Upconversion LO frequency (Hz)
)
"""
    results.append(test_snippet("7. MW-FEM output with upconverter", code7))

    # Test 8: OPX+ Analog output with filters
    print("Testing: OPX+ Analog output with filters...")
    code8 = """
from quam.components import BasicOPXPlusQuam
from quam.components.ports import OPXPlusPortsContainer

machine = BasicOPXPlusQuam(ports=OPXPlusPortsContainer())

# Analog output with filters
machine.ports.get_analog_output(
    "con1", 3,  # controller, port_id (note: only 2 elements)
    create=True,
    offset=0.2,
    feedforward_filter=[0.7, 0.2, 0.1],  # FIR filter
    feedback_filter=[0.3, 0.4, 0.5],  # IIR filter
)
"""
    results.append(test_snippet("8. OPX+ Analog output with filters", code8))

    # Test 9: Port Container Methods (FEM)
    print("Testing: Port Container Methods (FEM)...")
    code9 = """
from quam.components import BasicFEMQuam
from quam.components.ports import FEMPortsContainer

machine = BasicFEMQuam(ports=FEMPortsContainer())

# LF-FEM ports (3 parameters: controller, fem_id, port_id)
machine.ports.get_analog_output("con1", 1, 2, create=True)
machine.ports.get_analog_input("con1", 1, 1, create=True)
machine.ports.get_digital_output("con1", 1, 1, create=True)

# MW-FEM ports
machine.ports.get_mw_output("con1", 1, 1, create=True, band=1, upconverter_frequency=5e9)
machine.ports.get_mw_input("con1", 1, 1, create=True, band=1, downconverter_frequency=5e9)
"""
    results.append(test_snippet("9. Port Container Methods (FEM)", code9))

    # Test 10: Port Container Methods (OPX+)
    print("Testing: Port Container Methods (OPX+)...")
    code10 = """
from quam.components import BasicOPXPlusQuam
from quam.components.ports import OPXPlusPortsContainer

machine = BasicOPXPlusQuam(ports=OPXPlusPortsContainer())

machine.ports.get_analog_output("con1", 3, create=True)
machine.ports.get_digital_input("con1", 1, create=True)
"""
    results.append(test_snippet("10. Port Container Methods (OPX+)", code10))

    # Test 11: Port References with attribute linking
    print("Testing: Port References with attribute linking...")
    code11 = """
from quam.components import BasicFEMQuam
from quam.components.ports import FEMPortsContainer

machine = BasicFEMQuam(ports=FEMPortsContainer())

mw_output = machine.ports.get_mw_output("con1", 1, 1, create=True, band=1, upconverter_frequency=5e9)
mw_input = machine.ports.get_mw_input(
    "con1", 1, 1, create=True, band=1,
    downconverter_frequency=mw_output.get_reference("upconverter_frequency"),
)
"""
    results.append(test_snippet("11. Port References with attribute linking", code11))

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")

    passed_count = sum(1 for r in results if r.passed)
    serialization_passed_count = sum(1 for r in results if r.serialization_passed)

    for result in results:
        print(result)
        print()

    print("="*80)
    print(f"Execution: {passed_count}/{len(results)} tests passed")
    print(f"Serialization: {serialization_passed_count}/{len(results)} tests passed")
    print("="*80)

    # Return exit code based on results
    if passed_count == len(results) and serialization_passed_count == len(results):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
