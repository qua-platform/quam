from typing import Union, List

__all__ = [
    "ScalarInt",
    "ScalarFloat",
    "ScalarBool",
    "QuaScalarInt",
    "QuaScalarFloat",
    "QuaVariableInt",
    "QuaVariableFloat",
    "QuaVariable",
    "AmpValuesType",
    "ChirpType",
    "StreamType",
    "PulseAmp",
]

try:
    from qm.qua.type_hints import Scalar, QuaScalar, QuaVariable, ChirpType, StreamType

    ScalarInt = Scalar[int]
    ScalarFloat = Scalar[float]
    ScalarBool = Scalar[bool]
    QuaScalarInt = QuaScalar[int]

    QuaScalarFloat = QuaScalar[float]
    QuaVariable = QuaVariable
    QuaVariableBool = QuaVariable[bool]
    QuaVariableInt = QuaVariable[int]
    QuaVariableFloat = QuaVariable[float]
    PulseAmp = Union[Scalar[float], List[Scalar[float]]]

except ImportError:
    from qm.qua._dsl import (
        QuaNumberType,
        QuaVariableType,
        QuaExpressionType,
        ChirpType,
        StreamType,
        _PulseAmp,
        AmpValuesType,
    )

    ScalarInt = QuaNumberType
    ScalarFloat = QuaNumberType
    ScalarBool = QuaExpressionType
    QuaScalarInt = QuaNumberType
    QuaScalarFloat = QuaNumberType
    QuaVariable = QuaVariableType
    QuaVariableBool = QuaVariableType
    QuaVariableInt = QuaVariableType
    QuaVariableFloat = QuaVariableType
    PulseAmp = _PulseAmp
