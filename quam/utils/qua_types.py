__all__ = [
    "ScalarInt",
    "ScalarFloat",
    "ScalarBool",
    "QuaScalarInt",
    "QuaScalarFloat",
    "QuaVariableInt",
    "QuaVariableFloat",
    "AmpValuesType",
    "ChirpType",
    "StreamType",
    "_PulseAmp",
]

try:
    from qm.qua._expressions import Scalar, QuaScalar, QuaVariable

    ScalarInt = Scalar[int]
    ScalarFloat = Scalar[float]
    ScalarBool = Scalar[bool]
    QuaScalarInt = QuaScalar[int]
    QuaScalarFloat = QuaScalar[float]
    QuaVariableInt = QuaVariable[int]
    QuaVariableFloat = QuaVariable[float]
except ImportError:
    from qm.qua._dsl import QuaNumberType, QuaVariableType, QuaExpressionType

    ScalarInt = QuaNumberType
    ScalarFloat = QuaNumberType
    ScalarBool = QuaExpressionType
    QuaScalarInt = QuaNumberType
    QuaScalarFloat = QuaNumberType
    QuaVariableInt = QuaVariableType
    QuaVariableFloat = QuaVariableType


from qm.qua._dsl import (
    _PulseAmp,
    AmpValuesType,
    ChirpType,
    StreamType,
)
