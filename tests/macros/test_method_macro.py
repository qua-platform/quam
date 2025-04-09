from quam.core.macro.method_macro import MethodMacro, method_macro


class TestClass:
    def __init__(self, value: int):
        self.value = value

    @method_macro
    def add(self, x: int) -> int:
        return self.value + x


def test_method_macro_binding():
    """Test that MethodMacro correctly binds to instance methods"""
    obj = TestClass(5)
    assert isinstance(obj.add, MethodMacro)
    assert MethodMacro.is_macro_method(obj.add)
    assert obj.add.instance == obj


def test_method_macro_apply():
    """Test that MethodMacro.apply works with instance methods"""
    obj = TestClass(5)
    assert obj.add.apply(3) == 8  # 5 + 3
    assert obj.add(3) == 8  # Should work the same way


def test_is_macro_method():
    """Test the is_macro_method static method"""
    obj = TestClass(5)

    assert MethodMacro.is_macro_method(obj.add)
    assert not MethodMacro.is_macro_method(lambda x: x)
    assert not MethodMacro.is_macro_method(42)


def test_method_macro_preserves_metadata():
    """Test that MethodMacro preserves the original function's metadata"""

    def original(x: int) -> int:
        """Test docstring"""
        return x

    decorated = MethodMacro(original)
    assert decorated.__doc__ == original.__doc__
    assert decorated.__name__ == original.__name__
