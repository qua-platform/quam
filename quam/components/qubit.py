from typing import Dict, Union
from dataclasses import field

from quam.components.channels import Channel
from quam.core import quam_dataclass, QuamComponent
from .gates.single_qubit_gates import SingleQubitGate

from qm.qua._dsl import (
    AmpValuesType,
    QuaNumberType,
    QuaExpressionType,
    ChirpType,
    StreamType,
)


__all__ = ["Qubit"]


@quam_dataclass
class Qubit(QuamComponent):
    id: str
    gates: Dict[str, SingleQubitGate] = field(default_factory=dict)

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"

    def __matmul__(self, other):
        """Allows access to qubit pairs using the '@' operator, e.g. (q1 @ q2)"""
        if not isinstance(other, Qubit):
            raise ValueError(
                "Cannot create a qubit pair (q1 @ q2) with a non-qubit object, "
                f"where q1={self} and q2={other}"
            )

        if self is other:
            raise ValueError(
                "Cannot create a qubit pair with same qubit (q1 @ q1), where q1={self}"
            )

        if not hasattr(self._root, "qubit_pairs"):
            raise AttributeError(
                "Qubit pairs not found in the root component. "
                "Please add a 'qubit_pairs' attribute to the root component."
            )

        for qubit_pair in self._root.qubit_pairs:
            if qubit_pair.qubit_control is self and qubit_pair.qubit_target is other:
                return qubit_pair
        else:
            raise ValueError(
                "Qubit pair not found: qubit_control={self.name}, "
                "qubit_target={other.name}"
            )

    def play_pulse(
        self,
        pulse_name: str,
        amplitude_scale: Union[float, AmpValuesType] = None,
        duration: QuaNumberType = None,
        condition: QuaExpressionType = None,
        chirp: ChirpType = None,
        truncate: QuaNumberType = None,
        timestamp_stream: StreamType = None,
        continue_chirp: bool = False,
        target: str = "",
        validate: bool = True,
    ):
        """Play a pulse on the qubit, the corresponding channel will be determined
        based on the pulse name.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (float, _PulseAmp): Amplitude scale of the pulse.
                Can be either a float, or qua.amp(float).
            duration (int): Duration of the pulse in units of the clock cycle (4ns).
                If not provided, the default pulse duration will be used. It is possible
                to dynamically change the duration of both constant and arbitrary
                pulses. Arbitrary pulses can only be stretched, not compressed.
            chirp (Union[(list[int], str), (int, str)]): Allows to perform
                piecewise linear sweep of the element's intermediate
                frequency in time. Input should be a tuple, with the 1st
                element being a list of rates and the second should be a
                string with the units. The units can be either: 'Hz/nsec',
                'mHz/nsec', 'uHz/nsec', 'pHz/nsec' or 'GHz/sec', 'MHz/sec',
                'KHz/sec', 'Hz/sec', 'mHz/sec'.
            truncate (Union[int, QUA variable of type int]): Allows playing
                only part of the pulse, truncating the end. If provided,
                will play only up to the given time in units of the clock
                cycle (4ns).
            condition (A logical expression to evaluate.): Will play analog
                pulse only if the condition's value is true. Any digital
                pulses associated with the operation will always play.
            timestamp_stream (Union[str, _ResultSource]): (Supported from
                QOP 2.2) Adding a `timestamp_stream` argument will save the
                time at which the operation occurred to a stream. If the
                `timestamp_stream` is a string ``label``, then the timestamp
                handle can be retrieved with
                `qm._results.JobResults.get` with the same ``label``.
            validate (bool): If True (default), validate that the pulse is registered
                in Channel.operations

        Note:
            The `element` argument from `qm.qua.play()`is not needed, as it is
            automatically set to `self.name`.

        Raises:
            ValueError: If the pulse name is not found in any channel operations of the qubit.
        """
        attrs = self.get_attrs(follow_references=False, include_defaults=True)
        channels = {key: val for key, val in attrs.items() if isinstance(val, Channel)}
        for channel in channels.values():
            if pulse_name not in channel.operations:
                continue

            channel.play(
                pulse_name=pulse_name,
                amplitude_scale=amplitude_scale,
                duration=duration,
                condition=condition,
                chirp=chirp,
                truncate=truncate,
                timestamp_stream=timestamp_stream,
                continue_chirp=continue_chirp,
                target=target,
                validate=validate,
            )
            break
        else:
            raise ValueError(
                f"Pulse name not found in any channel operations of qubit: "
                f"{pulse_name=}\nqubit={self.name}"
            )
