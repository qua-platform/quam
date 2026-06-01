from typing import TypeAlias

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

    ScalarInt: TypeAlias = Scalar[int]
    ScalarFloat: TypeAlias = Scalar[float]
    ScalarBool: TypeAlias = Scalar[bool]
    QuaScalarInt: TypeAlias = QuaScalar[int]

    QuaScalarFloat: TypeAlias = QuaScalar[float]
    QuaVariableBool: TypeAlias = QuaVariable[bool]
    QuaVariableInt: TypeAlias = QuaVariable[int]
    QuaVariableFloat: TypeAlias = QuaVariable[float]

except ImportError:
    from qm.qua._dsl import (  # type: ignore[attr-defined, no-redef]
        QuaNumberType,
        QuaVariableType,
        QuaExpressionType,
        ChirpType,  # type: ignore[no-redef]
        StreamType,  # type: ignore[no-redef]
    )

    ScalarInt: TypeAlias = QuaNumberType  # type: ignore[misc, no-redef]
    ScalarFloat: TypeAlias = QuaNumberType  # type: ignore[misc, no-redef]
    ScalarBool: TypeAlias = QuaExpressionType  # type: ignore[misc, no-redef]
    QuaScalarInt: TypeAlias = QuaNumberType  # type: ignore[misc, no-redef]
    QuaScalarFloat: TypeAlias = QuaNumberType  # type: ignore[misc, no-redef]
    QuaVariable: TypeAlias = QuaVariableType  # type: ignore[no-redef]
    QuaVariableBool: TypeAlias = QuaVariableType  # type: ignore[misc, no-redef]
    QuaVariableInt: TypeAlias = QuaVariableType  # type: ignore[misc, no-redef]
    QuaVariableFloat: TypeAlias = QuaVariableType  # type: ignore[misc, no-redef]
