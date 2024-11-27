from quam.core import OperationsRegistry


def test_register_operations():
    operations_registry = OperationsRegistry()

    @operations_registry.register_operation
    def test_operation(a: int, b: int) -> int:
        return a + b

    assert dict(operations_registry) == {"test_operation": test_operation}

    assert test_operation(1, 2) == 3
    assert operations_registry["test_operation"](1, 2) == 3
