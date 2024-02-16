import os
from typing import Union, ClassVar, Dict
from dataclasses import field

from quam.core import QuamComponent, quam_dataclass
from quam.components.hardware import FrequencyConverter
from quam.components.channels import InOutIQChannel

from qm import QuantumMachinesManager
from qm import QuantumMachine
from qm.octave.qm_octave import QmOctave

from octave_sdk import RFInputLOSource
from qm.octave import QmOctaveConfig, RFOutputMode, ClockType


__all__ = ["OctaveOldFrequencyConverter", "OctaveOld"]


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
