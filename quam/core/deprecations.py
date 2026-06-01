import warnings
from abc import ABC, abstractmethod

instantiation_deprecations = []


class InstantiationDeprecationRule(ABC):
    @classmethod
    @abstractmethod
    def match(cls, quam_class, contents):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def apply(cls, quam_class, contents):
        raise NotImplementedError


class DeprecatedFrequencyConverterInstantiation(InstantiationDeprecationRule):
    @classmethod
    def match(cls, quam_class, contents):
        from quam.components.hardware import BaseFrequencyConverter

        if quam_class != BaseFrequencyConverter:
            return False
        if "__class__" in contents:
            return False
        return True

    @classmethod
    def apply(cls, quam_class, contents):
        from quam.components.hardware import FrequencyConverter

        warnings.warn(
            "The default frequency converter for channels is changed to the "
            "`BaseFrequencyConverter`. If you want to use `FrequencyConverter`, "
            'Please add {"__class__": "quam.components.hardware.FrequencyConverter"} '
            "to the JSON contents of the frequency converter. This will raise an error "
            "in future versions.",
            DeprecationWarning,
        )
        contents["__class__"] = "quam.components.hardware.FrequencyConverter"

        return FrequencyConverter, contents


instantiation_deprecations.append(DeprecatedFrequencyConverterInstantiation)
