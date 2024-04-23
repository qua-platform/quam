import pytest

from quam.components.hardware import FrequencyConverter, BaseFrequencyConverter
from quam.core.quam_instantiation import instantiate_quam_class
from quam.core.deprecations import DeprecatedFrequencyConverterInstantiation


def test_deprecation_frequency_converter():
    assert not DeprecatedFrequencyConverterInstantiation.match(FrequencyConverter, {})
    assert DeprecatedFrequencyConverterInstantiation.match(BaseFrequencyConverter, {})
    assert not DeprecatedFrequencyConverterInstantiation.match(
        BaseFrequencyConverter,
        {"__class__": "quam.components.hardware.FrequencyConverter"},
    )

    cls, contents = DeprecatedFrequencyConverterInstantiation.apply(
        BaseFrequencyConverter, {}
    )
    assert cls == FrequencyConverter
    assert contents == {"__class__": "quam.components.hardware.FrequencyConverter"}

    cls, contents = DeprecatedFrequencyConverterInstantiation.apply(
        BaseFrequencyConverter,
        {"__class__": "quam.components.hardware.BaseFrequencyConverter"},
    )
    assert cls == FrequencyConverter
    assert contents == {"__class__": "quam.components.hardware.FrequencyConverter"}


def test_instantiate_frequency_converter_deprecation():
    contents = {}
    with pytest.deprecated_call():
        obj = instantiate_quam_class(BaseFrequencyConverter, contents)

    assert isinstance(obj, FrequencyConverter)
    assert contents == {"__class__": "quam.components.hardware.FrequencyConverter"}
