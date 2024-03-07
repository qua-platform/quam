from abc import ABC
import os
from typing import Any, Optional, Union, ClassVar, Dict, List, Tuple, Literal
from dataclasses import field

from quam.core import QuamComponent, quam_dataclass
from quam.components.hardware import FrequencyConverter
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
    name: str
    ip: str
    port: int

    RF_outputs: Dict[int, "OctaveUpConverter"] = field(default_factory=dict)
    RF_inputs: Dict[int, "OctaveDownConverter"] = field(default_factory=dict)
    loopbacks: List[Tuple[Tuple[str, str], str]] = field(default_factory=list)

    def initialize_default_connectivity(self):
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
        octave_config.add_device_info(self.name, self.ip, self.port)
        return octave_config

    def apply_to_config(self, config: Dict) -> None:
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
            "loopbacks": self.loopbacks,
        }


@quam_dataclass
class OctaveFrequencyConverter(FrequencyConverter, ABC):
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
        return {"after": [self.octave]}

    def apply_to_config(self, config: Dict) -> None:
        super().apply_to_config(config)  # TODO is this necessary?

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
    gain: float = 0  # range [-20:0.5:20]
    LO_source: Literal["internal", "external"] = "internal"
    LO_frequency: float  # Between 2 and 18 GHz
    output_mode: Literal[
        "always_on", "always_off", "triggered", "triggered_reersed"
    ] = "always_on"
    input_attenuators: Literal["off", "on"] = "off"

    def apply_to_config(self, config: Dict) -> None:
        super().apply_to_config(config)

        if self.id in config["octaves"][self.octave.name]["RF_outputs"]:
            raise KeyError(
                f"Error generating config: "
                f'config["octaves"]["{self.octave.name}"]["RF_inputs"] '
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
            output_config["I_connection"] = self.channel.opx_output
        elif isinstance(self.channel, IQChannel):
            output_config["I_connection"] = self.channel.opx_output_I
            output_config["Q_connection"] = self.channel.opx_output_Q


@quam_dataclass
class OctaveDownConverter(OctaveFrequencyConverter):
    LO_frequency: float  # Between 2 and 18 GHz
    LO_source: Literal["internal", "external"] = (
        "internal"  # default is internal for LO 1, external for LO 2
    )
    IF_mode_I: Literal["direct", "envelope", "mixer", "off"] = "direct"
    IF_mode_Q: Literal["direct", "envelope", "mixer", "off"] = "direct"
    IF_output_I: Literal[1, 2] = 1
    IF_output_Q: Literal[1, 2] = 2

    @property
    def config_settings(self):
        return {"after": self.octave}

    def apply_to_config(self, config: Dict) -> None:
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

        IF_config = config["octaves"][self.octave.name]["IF_outputs"]
        for k, (IF_ch, opx_ch) in enumerate(zip(IF_channels, opx_channels), start=1):
            label = f"IF_out{IF_ch}"
            IF_config.setdefault(label, {"port": tuple(opx_ch), "name": f"out{k}"})
            if IF_config[label]["port"] != tuple(opx_ch):
                raise ValueError(
                    f"Error generating config for Octave downconverter id={self.id}: "
                    f"Unable to assign {label} to  port {opx_ch} because it is already "
                    f"assigned to port {IF_config[label]['port']} "
                )


@quam_dataclass
class OctaveOld(QuamComponent):
    name: str
    host: str
    port: int
    qmm_host: str
    qmm_port: int

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
            host=self.qmm_host, port=self.qmm_port, octave=self.octave_config
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
            if getattr(elem.frequency_converter_down, "octave") is not self:
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
