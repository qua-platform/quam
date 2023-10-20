import numpy as np
from typing import List
from dataclasses import dataclass

from quam.core import QuamComponent
from quam.utils import patch_dataclass
from quam.utils import string_reference as str_ref


patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10


__all__ = [
    "LocalOscillator",
    "Mixer",
]


@dataclass(kw_only=True, eq=False)
class LocalOscillator(QuamComponent):
    """QuAM component for a local oscillator.

    Args:
        frequency (float): The frequency of the local oscillator.
            Used by the mixer to determine the intermediate frequency.
        power (float, optional): The power of the local oscillator.
            Not used for the QUA configuration
    """

    frequency: float
    power: float = None


@dataclass(kw_only=True, eq=False)
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
        offset_I (float, optional): The offset of the I channel. Default is 0.
        offset_Q (float, optional): The offset of the Q channel. Default is 0.
        correction_gain (float, optional): The gain imbalance of the mixer.
            Default is 0, see `Mixer.IQ_imbalance` for details.
        correction_phase (float, optional): The phase imbalance of the mixer in radians.
    """

    local_oscillator_frequency: float = "#../local_oscillator/frequency"
    intermediate_frequency: float = "#../intermediate_frequency"

    offset_I: float = 0
    offset_Q: float = 0

    correction_gain: float = 0
    correction_phase: float = 0

    @property
    def name(self):
        parent_id = self._get_referenced_value("#../name")
        if str_ref.is_reference(parent_id):
            raise AttributeError(f"Mixer.parent must be defined for {self}")
        return f"{parent_id}{str_ref.DELIMITER}mixer"

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
