from typing import Callable
import pytest
from quam.components.basic_quam import BasicFEMQuam
from quam.components.ports import LFFEMAnalogOutputPort, LFFEMAnalogInputPort


def make_lf_output_port(port_id: int = 1) -> LFFEMAnalogOutputPort:
    return LFFEMAnalogOutputPort("con1", 1, port_id)


def make_lf_input_port(port_id: int = 1) -> LFFEMAnalogInputPort:
    return LFFEMAnalogInputPort("con1", 1, port_id)


@pytest.fixture
def base_machine():
    return BasicFEMQuam()


@pytest.fixture
def validate_quam_config(qmm, base_machine):
    def _validate(setup_fn: Callable[[BasicFEMQuam], None]) -> None:
        setup_fn(base_machine)
        config = base_machine.generate_config()
        qm = qmm.open_qm(config)
        qm.close()

    return _validate
