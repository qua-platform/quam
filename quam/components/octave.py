from abc import ABC
import os
from typing import Any, Optional, Union, ClassVar, Dict, List, Tuple, Literal
from dataclasses import field

from quam.components.ports.analog_outputs import LFAnalogOutputPort
from quam.components.ports.base_ports import BasePort
from quam.core import QuamComponent, quam_dataclass
from quam.components.hardware import BaseFrequencyConverter, FrequencyConverter
from quam.components.channels import (
    Channel,
    IQChannel,
    InOutIQChannel,
    InOutSingleChannel,
    SingleChannel,
)

from qm import QuantumMachinesManager, QuantumMachine
from qm.octave import QmOctaveConfig, RFOutputMode, ClockType
from qm.octave.qm_octave import QmOctave


__all__ = [
    "Octave",
    "OctaveUpConverter",
    "OctaveDownConverter",
    "OctaveOldFrequencyConverter",
    "OctaveOld",
]


@quam_dataclass
class Octave(QuamComponent):
    """QuAM component for the QM Octave.

    The QM Octave is a device that can be used to upconvert and downconvert signals. It
    has 5 RF outputs and 2 RF inputs. Each RF_output has an associated
    `OctaveUpConverter`, and similarly each RF_input has an `OctaveDownConverter`.

    In many cases the Octave is connected to a single OPX in the default configuration,
    i.e. OPX outputs are connected to the corresponding Octave I/Q input, and Octave IF
    outputs are connected to the corresponding OPX input. In this case you can configure
    the Octave with the correct `FrequencyConverter`s using
    `Octave.initialize_default_connectivity()`.

    Args:
        name: The name of the Octave. Must be unique
        ip: The IP address of the Octave. Used in `Octave.get_octave_config()`
        port: The port number of the Octave. Used in `Octave.get_octave_config()`
        calibration_db_path: The path to the calibration database. If not specified, the
            current working directory is used.
        RF_outputs: A dictionary of `OctaveUpConverter` objects. The keys are the
            output numbers (1-5).
        RF_inputs: A dictionary of `OctaveDownConverter` objects. The keys are the
            input numbers (1-2).
        loopbacks: A list of loopback connections, for example to connect a local
            oscillator. See the QUA Octave documentation for details.
    """

    name: str
    ip: str
    port: int
    calibration_db_path: str = None

    RF_outputs: Dict[int, "OctaveUpConverter"] = field(default_factory=dict)
    RF_inputs: Dict[int, "OctaveDownConverter"] = field(default_factory=dict)
    loopbacks: List[Tuple[Tuple[str, str], str]] = field(default_factory=list)

    def initialize_frequency_converters(self):
        """Initialize the Octave frequency converterswith default connectivity.

        This method initializes the Octave with default connectivity, i.e. it connects
        the Octave to a single OPX. It creates an `OctaveUpConverter` for each RF output
        and an `OctaveDownConverter` for each RF input. The `OctaveUpConverter` objects
        are added to `Octave.RF_outputs` and the `OctaveDownConverter` objects are added
        to `Octave.RF_inputs`.

        Raises:
            ValueError: If the Octave already has RF_outputs or RF_inputs.

        """
        if self.RF_outputs:
            raise ValueError(
                "Error initializing Octave with default connectivity. "
                "octave.RF_outputs is not empty"
            )
        if self.RF_inputs:
            raise ValueError(
                "Error initializing Octave with default connectivity. "
                "octave.IF_outputs is not empty"
            )

        for idx in range(1, 6):
            self.RF_outputs[idx] = OctaveUpConverter(
                id=idx,
                LO_frequency=None,  # TODO What should default be?
            )

        for idx in range(1, 3):
            self.RF_inputs[idx] = OctaveDownConverter(id=idx, LO_frequency=None)

    def get_octave_config(self) -> QmOctaveConfig:
        """Return a QmOctaveConfig object with the current Octave configuration."""
        octave_config = QmOctaveConfig()

        if self.calibration_db_path is not None:
            octave_config.set_calibration_db(self.calibration_db_path)
        else:
            octave_config.set_calibration_db(os.getcwd())

        octave_config.add_device_info(self.name, self.ip, self.port)
        return octave_config

    def apply_to_config(self, config: Dict) -> None:
        """Add the Octave configuration to a config dictionary.

        This method is called by the `QuamComponent.generate_config` method.

        Args:
            config: A dictionary representing a QUA config file.

        Raises:
            KeyError: If the Octave is already in the config.
        """
        if "octaves" not in config:
            config["octaves"] = {}
        if self.name in config["octaves"]:
            raise KeyError(
                f'Error generating config: config["octaves"] already contains an entry '
                f' for Octave "{self.name}"'
            )

        config["octaves"][self.name] = {
            "RF_outputs": {},
            "IF_outputs": {},
            "RF_inputs": {},
            "loopbacks": list(self.loopbacks),
        }


@quam_dataclass
class OctaveFrequencyConverter(BaseFrequencyConverter, ABC):
    """Base class for OctaveUpConverter and OctaveDownConverter.

    Args:
        id: The id of the converter. Must be unique within the Octave.
            For OctaveUpConverter, the id is used as the RF output number.
            For OctaveDownConverter, the id is used as the RF input number.
        channel: The channel that the converter is connected to.
    """

    id: int
    channel: Channel = None

    @property
    def octave(self) -> Optional[Octave]:
        if self.parent is None:
            return None
        parent_parent = getattr(self.parent, "parent")
        if not isinstance(parent_parent, Octave):
            return None
        return parent_parent

    @property
    def config_settings(self) -> Dict[str, Any]:
        """Specifies that the converter will be added to the config after the Octave."""
        return {"after": [self.octave]}

    def apply_to_config(self, config: Dict) -> None:
        """Add information about the frequency converter to the QUA config

        This method is called by the `QuamComponent.generate_config` method.

        Args:
            config: A dictionary representing a QUA config file.

        Raises:
            KeyError: If the Octave is not in the config, or if config["octaves"] does
                not exist.
        """
        super().apply_to_config(config)

        if "octaves" not in config:
            raise KeyError('Error generating config: "octaves" entry not found')

        if self.octave is None:
            raise KeyError(
                f"Error generating config: OctaveConverter with id {self.id} does not "
                "have an Octave parent"
            )

        if self.octave.name not in config["octaves"]:
            raise KeyError(
                'Error generating config: config["octaves"] does not have Octave'
                f' entry config["octaves"]["{self.octave.name}"]'
            )


@quam_dataclass
class OctaveUpConverter(OctaveFrequencyConverter):
    """A frequency upconverter for the QM Octave.

    The OctaveUpConverter represents a frequency upconverter in the QM Octave. Usually
    an IQChannel is connected `OctaveUpconverter.channel`, in which case the two OPX
    outputs are connected to the I and Q inputs of the OctaveUpConverter.
    The OPX outputs are specified in the `OctaveUpConverter.channel` attribute.
    The channel is either an IQChannel or a SingleChannel.

    Args:
        id: The RF output id, must be between 1-5.
        LO_frequency: The local oscillator frequency in Hz, between 2 and 18 GHz.
        LO_source: The local oscillator source, "internal" (default) or "external".
        gain: The gain of the output, between -20 and 20 dB in steps of 0.5.
            Default is 0 dB.
        output_mode: Sets the fast switch's mode of the up converter module.
            Can be "always_on" / "always_off" / "triggered" / "triggered_reversed".
            The default is "always_off".
            - "always_on" - Output is always on
            - "always_off" - Output is always off
            - "triggered" - The output will play when rising edge is detected in the
              octave's digital port.
            - "triggered_reversed" - The output will play when falling edge is detected
              in the octave's digital port.
        input_attenuators: Whether the I and Q ports have a 10 dB attenuator before
            entering the mixer. Off by default.
    """

    LO_frequency: float = None
    LO_source: Literal["internal", "external"] = "internal"
    gain: float = 0
    output_mode: Literal[
        "always_on", "always_off", "triggered", "triggered_reversed"
    ] = "always_off"
    input_attenuators: Literal["off", "on"] = "off"

    def apply_to_config(self, config: Dict) -> None:
        """Add information about the frequency up-converter to the QUA config

        This method is called by the `QuamComponent.generate_config` method.

        Nothing is added to the config if the `OctaveUpConverter.channel` is not
        specified or if the `OctaveUpConverter.LO_frequency` is not specified.

        Args:
            config: A dictionary representing a QUA config file.

        Raises:
            ValueError: If the LO_frequency is not specified.
            KeyError: If the Octave is not in the config, or if config["octaves"] does
                not exist.
            KeyError: If the Octave already has an entry for the OctaveUpConverter.
        """
        if not isinstance(self.LO_frequency, (int, float)):
            if self.channel is None:
                return
            else:
                raise ValueError(
                    f"Error generating config for Octave upconverter id={self.id}: "
                    "LO_frequency must be specified."
                )

        super().apply_to_config(config)

        if self.id in config["octaves"][self.octave.name]["RF_outputs"]:
            raise KeyError(
                f"Error generating config: "
                f'config["octaves"]["{self.octave.name}"]["RF_outputs"] '
                f'already has an entry for OctaveDownConverter with id "{self.id}"'
            )

        output_config = config["octaves"][self.octave.name]["RF_outputs"][self.id] = {
            "LO_frequency": self.LO_frequency,
            "LO_source": self.LO_source,
            "gain": self.gain,
            "output_mode": self.output_mode,
            "input_attenuators": self.input_attenuators,
        }
        if isinstance(self.channel, SingleChannel):
            if isinstance(self.channel.opx_output, LFAnalogOutputPort):
                output_config["I_connection"] = self.channel.opx_output.port_tuple
            else:
                output_config["I_connection"] = self.channel.opx_output
        elif isinstance(self.channel, IQChannel):
            if isinstance(self.channel.opx_output_I, LFAnalogOutputPort):
                output_config["I_connection"] = self.channel.opx_output_I.port_tuple
            else:
                output_config["I_connection"] = tuple(self.channel.opx_output_I)
            if isinstance(self.channel.opx_output_Q, LFAnalogOutputPort):
                output_config["Q_connection"] = self.channel.opx_output_Q.port_tuple
            else:
                output_config["Q_connection"] = tuple(self.channel.opx_output_Q)


@quam_dataclass
class OctaveDownConverter(OctaveFrequencyConverter):
    """A frequency downconverter for the QM Octave.

    The OctaveDownConverter represents a frequency downconverter in the QM Octave. The
    OctaveDownConverter is usually connected to an InOutIQChannel, in which case the
    two OPX inputs are connected to the IF outputs of the OctaveDownConverter. The
    OPX inputs are specified in the `OctaveDownConverter.channel` attribute. The
    channel is either an InOutIQChannel or an InOutSingleChannel.

    Args:
        id: The RF input id, must be between 1-2.
        LO_frequency: The local oscillator frequency in Hz, between 2 and 18 GHz.
        LO_source: The local oscillator source, "internal" or "external.
            For down converter 1 "internal" is the default,
            for down converter 2 "external" is the default.
        IF_mode_I: Sets the mode of the I port of the IF Down Converter module as can be
            seen in the octave block diagram (see Octave page in QUA documentation).
            Can be "direct" / "envelope" / "mixer" / "off". The default is "direct".
            - "direct" - The signal bypasses the IF module.
            - "envelope" - The signal passes through an envelope detector.
            - "mixer" - The signal passes through a low-frequency mixer.
            - "off" - the signal doesn't pass to the output port.
        IF_mode_Q: Sets the mode of the Q port of the IF Down Converter module.
        IF_output_I: The output port of the IF Down Converter module for the I port.
            Can be 1 or 2. The default is 1. This will be 2 if the IF outputs
            are connected to the opposite OPX inputs
        IF_output_Q: The output port of the IF Down Converter module for the Q port.
            Can be 1 or 2. The default is 2. This will be 1 if the IF outputs
            are connected to the opposite OPX inputs.
    """

    LO_frequency: float = None
    LO_source: Literal["internal", "external"] = "internal"
    IF_mode_I: Literal["direct", "envelope", "mixer", "off"] = "direct"
    IF_mode_Q: Literal["direct", "envelope", "mixer", "off"] = "direct"
    IF_output_I: Literal[1, 2] = 1
    IF_output_Q: Literal[1, 2] = 2

    @property
    def config_settings(self):
        """Specifies that the converter will be added to the config after the Octave."""
        return {"after": [self.octave]}

    def apply_to_config(self, config: Dict) -> None:
        """Add information about the frequency down-converter to the QUA config

        This method is called by the `QuamComponent.generate_config` method.

        Nothing is added to the config if the `OctaveDownConverter.channel` is not
        specified or if the `OctaveDownConverter.LO_frequency` is not specified.

        Args:
            config: A dictionary representing a QUA config file.

        Raises:
            ValueError: If the LO_frequency is not specified.
            KeyError: If the Octave is not in the config, or if config["octaves"] does
                not exist.
            KeyError: If the Octave already has an entry for the OctaveDownConverter.
            ValueError: If the IF_output_I and IF_output_Q are already assigned to
                other ports.
        """
        if not isinstance(self.LO_frequency, (int, float)):
            if self.channel is None:
                return
            else:
                raise ValueError(
                    f"Error generating config for Octave upconverter id={self.id}: "
                    "LO_frequency must be specified."
                )

        super().apply_to_config(config)

        if self.id in config["octaves"][self.octave.name]["RF_inputs"]:
            raise KeyError(
                f"Error generating config: "
                f'config["octaves"]["{self.octave.name}"]["RF_inputs"] '
                f'already has an entry for OctaveDownConverter with id "{self.id}"'
            )

        config["octaves"][self.octave.name]["RF_inputs"][self.id] = {
            "RF_source": "RF_in",
            "LO_frequency": self.LO_frequency,
            "LO_source": self.LO_source,
            "IF_mode_I": self.IF_mode_I,
            "IF_mode_Q": self.IF_mode_Q,
        }

        if isinstance(self.channel, InOutIQChannel):
            IF_channels = [self.IF_output_I, self.IF_output_Q]
            opx_channels = [self.channel.opx_input_I, self.channel.opx_input_Q]
        elif isinstance(self.channel, InOutSingleChannel):
            IF_channels = [self.IF_output_I]
            opx_channels = [self.channel.opx_input]
        else:
            IF_channels = []
            opx_channels = []

        opx_port_tuples = [
            p.port_tuple if isinstance(p, BasePort) else tuple(p) for p in opx_channels
        ]

        IF_config = config["octaves"][self.octave.name]["IF_outputs"]
        for k, (IF_ch, opx_port_tuples) in enumerate(
            zip(IF_channels, opx_port_tuples), start=1
        ):
            label = f"IF_out{IF_ch}"
            IF_config.setdefault(label, {"port": opx_port_tuples, "name": f"out{k}"})
            if IF_config[label]["port"] != opx_port_tuples:
                raise ValueError(
                    f"Error generating config for Octave downconverter id={self.id}: "
                    f"Unable to assign {label} to  port {opx_port_tuples} because it is already "
                    f"assigned to port {IF_config[label]['port']} "
                )


@quam_dataclass
class OctaveOld(QuamComponent):
    name: str
    host: str
    port: int
    qmm_host: str
    qmm_port: int
    connection_headers: Dict[str, str] = None

    calibration_db: str = None

    octave_config: ClassVar[QmOctaveConfig] = None
    _qms: ClassVar[Dict[str, QuantumMachinesManager]] = {}
    _qm: ClassVar[QuantumMachine] = None
    octave: ClassVar[QmOctave] = None
    _channel_to_qe: ClassVar[dict] = None

    def _initialize_config(self):
        calibration_db = self.calibration_db
        if calibration_db is None:
            calibration_db = os.getcwd()

        octave_config = QmOctaveConfig()
        octave_config.set_calibration_db(calibration_db)
        octave_config.add_device_info(self.name, self.host, self.port)

        portmap = self.get_portmap()
        octave_config.add_opx_octave_port_mapping(portmap)

        return octave_config

    def _initialize_qm(self) -> QuantumMachine:
        qmm = QuantumMachinesManager(
            host=self.qmm_host,
            port=self.qmm_port,
            octave=self.octave_config,
            connection_headers=self.connection_headers,
        )
        qm = qmm.open_qm(self._root.generate_config())
        return qm

    def get_portmap(self):
        portmap = {}

        if self._channel_to_qe is None:
            self._channel_to_qe = {}

        for elem in self._root.iterate_components():
            if not isinstance(elem, OctaveOldFrequencyConverter):
                continue

            if elem.octave is not self:
                continue

            channel = elem.parent
            portmap[tuple(channel.opx_output_I)] = (self.name, f"I{elem.channel}")
            portmap[tuple(channel.opx_output_Q)] = (self.name, f"Q{elem.channel}")
            self._channel_to_qe[(self.name, elem.channel)] = channel.name
        return portmap

    def configure_octave_settings(self):
        from octave_sdk import RFInputLOSource

        self.octave.set_clock(self.name, ClockType.Internal)
        for qe in self._channel_to_qe.values():
            self.octave.set_rf_output_mode(qe, RFOutputMode.on)

        for elem in self._root.iterate_components():
            if not isinstance(elem, InOutIQChannel):
                continue
            if getattr(elem.frequency_converter_down, "octave", None) is not self:
                continue

            self.octave.set_qua_element_octave_rf_in_port(elem.name, self.name, 1)
            self.octave.set_downconversion(
                elem.name, lo_source=RFInputLOSource.Internal
            )

    def configure(self):
        self.octave_config = self._initialize_config()

        if self.name not in self._qms:
            self.qm = self._qms[self.name] = self._initialize_qm()
            self.octave = self.qm.octave

        else:
            self.qm = self._qms[self.name]
            self.octave = self.qm.octave
            # self.configure_octave_settings()
            # self.octave_config = self.octave._octave_manager._octave_config

        self.configure_octave_settings()

    def calibrate(self, channel: str, lo_freq: int, if_freq: int, gain: float):
        channel_qe = self._channel_to_qe[self.name, channel]
        self.octave.set_lo_frequency(channel_qe, lo_freq)
        self.octave.set_rf_output_gain(channel_qe, gain)
        self.octave.set_rf_output_mode(channel_qe, RFOutputMode.on)
        self.octave.set_clock(self.name, ClockType.Internal)
        self.octave.calibrate_element(channel_qe, [(lo_freq, if_freq)])

    def set_frequency(self, channel: str, frequency: float):
        channel_qe = self._channel_to_qe[self.name, channel]
        self.octave.set_lo_frequency(channel_qe, frequency)

    def set_gain(self, channel: str, gain: float):
        channel_qe = self._channel_to_qe[self.name, channel]
        self.octave.set_rf_output_gain(channel_qe, gain)


@quam_dataclass
class OctaveOldFrequencyConverter(FrequencyConverter):
    channel: Union[str, int]
    octave: OctaveOld

    @property
    def frequency(self):
        return self.local_oscillator.frequency

    def configure(self):
        self.octave.set_frequency(channel=self.channel, frequency=self.frequency)
        if self.gain is not None:
            self.octave.set_gain(channel=self.channel, gain=self.gain)
