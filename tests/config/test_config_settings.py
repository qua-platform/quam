from dataclasses import dataclass

from quam.core import QuamComponent, QuamRoot


@dataclass
class Component(QuamComponent):
    name: str

    def apply_to_config(self, config: dict) -> None:
        config.setdefault("list", [])
        config["list"].append(self.name)


@dataclass
class Root(QuamRoot):
    first_component: Component
    second_component: Component


def test_generate_basic_config():
    root = Root(
        first_component=Component(name="first"),
        second_component=Component(name="second"),
    )
    config = root.generate_config()
    assert config["list"] == ["first", "second"]


def test_generate_after():
    root = Root(
        first_component=Component(name="first"),
        second_component=Component(name="second"),
    )

    root.first_component.config_settings = {"after": "#/second_component"}

    config = root.generate_config()
    assert config["list"] == ["second", "first"]


def test_generate_before():
    root = Root(
        first_component=Component(name="first"),
        second_component=Component(name="second"),
    )

    root.second_component.config_settings = {"after": "#/first_component"}

    config = root.generate_config()
    assert config["list"] == ["second", "first"]


def test_generate_after_property():
    @dataclass
    class ComponentProperty(QuamComponent):
        name: str

        def apply_to_config(self, config: dict) -> None:
            config.setdefault("list", [])
            config["list"].append(self.name)

        @property
        def config_settings(self):
            return {"after": self._root.second_component}

    root = Root(
        first_component=ComponentProperty(name="first"),
        second_component=Component(name="second"),
    )

    config = root.generate_config()
    assert config["list"] == ["second", "first"]
