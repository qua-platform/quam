__all__ = [
    "ScalarInt",
    "ScalarFloat",
    "ScalarBool",
    "QuaScalarInt",
    "QuaScalarFloat",
    "QuaVariableInt",
    "QuaVariableFloat",
    "QuaVariable",
    "ChirpType",
    "StreamType",
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

except ImportError:
    from qm.qua._dsl import (
        QuaNumberType,
        QuaVariableType,
        QuaExpressionType,
        ChirpType,
        StreamType,
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

