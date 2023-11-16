import numpy as np
import os
from typing import List, Union, ClassVar, Dict
from dataclasses import dataclass, field

from quam.core import QuamComponent
from quam.utils import patch_dataclass
from quam.components.hardware import LocalOscillator, Mixer, FrequencyConverter


from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.QuantumMachine import QuantumMachine
from qm.octave.qm_octave import QmOctave

from octave_sdk import RFInputLOSource
from qm.octave import QmOctaveConfig, RFOutputMode, ClockType


__al__ = ["OctaveFrequencyConverter", "OctaveOld"]


@dataclass(kw_only=True, eq=False)
class OctaveFrequencyConverter(FrequencyConverter):
    channel: Union[str, int]


@dataclass
class OctaveOld(QuamComponent):
    name: str
    host: str
    port: int
    qmm_host: str
    qmm_port: int

    calibration_db: str = None

    octave_config: QmOctaveConfig = None
    _qms: ClassVar[Dict[str, QuantumMachinesManager]] = {}
    _qm: QuantumMachine = None
    octave: QmOctave = None
    _channel_to_qe: dict = field(default_factory=dict)

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

        for q in self._root.active_qubits:
            if q.xy.local_oscillator.frequency_converter is self:
                xy_LO_channel = q.xy.local_oscillator.channel
                portmap[tuple(q.xy.output_port_I)] = (self.name, f"I{xy_LO_channel}")
                portmap[tuple(q.xy.output_port_Q)] = (self.name, f"Q{xy_LO_channel}")
                self._channel_to_qe[(self.name, xy_LO_channel)] = q.xy.name

            if q.rr.local_oscillator.frequency_converter is self:
                rr_LO_channel = q.rr.local_oscillator.channel
                portmap[tuple(q.rr.output_port_I)] = (self.name, f"I{rr_LO_channel}")
                portmap[tuple(q.rr.output_port_Q)] = (self.name, f"Q{rr_LO_channel}")
                self._channel_to_qe[(self.name, rr_LO_channel)] = q.rr.name

        return portmap

    def configure_octave_settings(self):
        self.octave.set_clock(self.name, ClockType.Internal)
        for qe in self._channel_to_qe.values():
            self.octave.set_rf_output_mode(qe, RFOutputMode.on)
        for q in self._root.active_qubits:
            if q.rr.local_oscillator.frequency_converter is self:
                self.octave.set_qua_element_octave_rf_in_port(q.rr.name, self.name, 1)
                self.octave.set_downconversion(
                    q.rr.name, lo_source=RFInputLOSource.Internal
                )

    def configure(self):
        if self.name not in self._qms:
            self.octave_config = self._initialize_config()
            self.qm = self._qms[self.name] = self._initialize_qm()
            self.octave = self.qm.octave
        else:
            self.qm = self._qms[self.name]
            self.octave = self.qm.octave
            self.octave_config = self.qm._octave_config

        self.configure_octave_settings()

    def calibrate(self, channel: str, lo_freq: int, if_freq: int, gain: float):
        channel_qe = self._channel_to_qe[self.name, channel]
        self.octave.set_lo_frequency(channel_qe, lo_freq)
        self.octave.set_rf_output_gain(channel_qe, gain)
        self.octave.set_rf_output_mode(channel_qe, RFOutputMode.on)
        self.octave.set_clock(self.name, ClockType.Internal)
        self.octave.calibrate_element(channel_qe, [(lo_freq, if_freq)])

    def set_frequency(self, channel: str, freq: float):
        channel_qe = self._channel_to_qe[self.name, channel]
        self.octave.set_lo_frequency(channel_qe, freq)

    def set_gain(self, channel: str, gain: float):
        channel_qe = self._channel_to_qe[self.name, channel]
        self.octave.set_rf_output_gain(channel_qe, gain)
