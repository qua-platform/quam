import numpy as np
from typing import List

from quam.core import QuamComponent, quam_dataclass
from quam.utils import string_reference as str_ref


__all__ = [
    "LocalOscillator",
    "Mixer",
    "FrequencyConverter",
]


@quam_dataclass
class LocalOscillator(QuamComponent):
    """QuAM component for a local oscillator.

    Args:
        frequency (float): The frequency of the local oscillator.
            Used by the mixer to determine the intermediate frequency.
        power (float, optional): The power of the local oscillator.
            Not used for the QUA configuration
    """

    frequency: float = None
    power: float = None

    def configure(self): ...


@quam_dataclass
class Mixer(QuamComponent):
    """QuAM component for a mixer.

    All properties are optional, so it can be instantiated as `Mixer()`.
    For the default values, it is assumed that the mixer parent is an `IQChannel`
    that has a `LocalOscillator`.

    Args:
        local_oscillator_frequency (float, optional): The frequency of the local
            oscillator. Default is `#../local_oscillator/frequency`, meaning that
            the frequency is extracted from the the local_oscillator of the parent.
        intermediate_frequency (float, optional): The intermediate frequency of the
            mixer. Default is `#../intermediate_frequency`, meaning that the frequency
            references the intermediate_frequency of the parent.
        correction_gain (float, optional): The gain imbalance of the mixer.
            Default is 0, see `Mixer.IQ_imbalance` for details.
        correction_phase (float, optional): The phase imbalance of the mixer in radians.
    """

    local_oscillator_frequency: float = "#../local_oscillator/frequency"
    intermediate_frequency: float = "#../../intermediate_frequency"

    correction_gain: float = 0
    correction_phase: float = 0

    @property
    def name(self):
        frequency_converter = getattr(self, "parent", None)
        if frequency_converter is None:
            raise AttributeError(
                f"Mixer.parent must be a frequency converter for {self}"
            )

        channel = getattr(frequency_converter, "parent", None)
        channel_name = getattr(channel, "name", None)
        if channel is None or channel_name is None:
            raise AttributeError(f"Mixer.parent.parent must be a channel for {self}")

        return f"{channel_name}{str_ref.DELIMITER}mixer"

    def apply_to_config(self, config: dict):
        """Adds this mixer to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        correction_matrix = self.IQ_imbalance(
            self.correction_gain, self.correction_phase
        )

        config["mixers"][self.name] = [
            {
                "intermediate_frequency": self.intermediate_frequency,
                "lo_frequency": self.local_oscillator_frequency,
                "correction": correction_matrix,
            }
        ]

    @staticmethod
    def IQ_imbalance(g: float, phi: float) -> List[float]:
        """
        Creates the correction matrix for the mixer imbalance caused by the gain and
        phase imbalances, more information can be seen here:
        https://docs.qualang.io/libs/examples/mixer-calibration/#non-ideal-mixer
        :param g: relative gain imbalance between the I & Q ports. (unit-less),
            set to 0 for no gain imbalance.
        :param phi: relative phase imbalance between the I & Q ports (radians),
            set to 0 for no phase imbalance.
        """
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [
            float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]
        ]


@quam_dataclass
class BaseFrequencyConverter(QuamComponent):
    """Base class for frequency converters."""

    pass


@quam_dataclass
class FrequencyConverter(BaseFrequencyConverter):
    """Frequency up/down converter component.

    This component encapsulates the local oscillator and mixer used to upconvert or
    downconvert an RF signal.

    The FrequencyConverter component is attached to IQ channels through

    - `IQChannel.frequency_converter_up`
    - `InOutIQChannel.frequency_converter_down`

    Args:
        local_oscillator (LocalOscillator): The local oscillator for the frequency converter.
        mixer (Mixer): The mixer for the frequency converter.
        gain (float): The gain of the frequency converter.
    """

    local_oscillator: LocalOscillator = None
    mixer: Mixer = None
    gain: float = None

    @property
    def LO_frequency(self):
        return self.local_oscillator.frequency

    def configure(self):
        if self.local_oscillator is not None:
            self.local_oscillator.configure()
