from typing import ClassVar, Dict, Optional, TypeVar, Union
from dataclasses import field
from quam.components.ports.base_ports import FEMPort
from quam.core import quam_dataclass, QuamComponent
from quam.core.quam_classes import QuamBase
from .analog_outputs import (
    OPXPlusAnalogOutputPort,
    LFFEMAnalogOutputPort,
    MWFEMAnalogOutputPort,
)
from .analog_inputs import (
    OPXPlusAnalogInputPort,
    LFFEMAnalogInputPort,
    MWFEMAnalogInputPort,
)
from .digital_outputs import OPXPlusDigitalOutputPort, FEMDigitalOutputPort
from .digital_inputs import OPXPlusDigitalInputPort


__all__ = ["OPXPlusPortsContainer", "FEMPortsContainer"]

OPXPlusPortTypes = Union[
    OPXPlusAnalogInputPort,
    OPXPlusAnalogOutputPort,
    OPXPlusDigitalOutputPort,
    OPXPlusDigitalInputPort,
]
FEMPortTypes = Union[
    LFFEMAnalogInputPort,
    LFFEMAnalogOutputPort,
    MWFEMAnalogInputPort,
    MWFEMAnalogOutputPort,
    FEMDigitalOutputPort,
]


@quam_dataclass
class OPXPlusPortsContainer(QuamComponent):
    analog_outputs: Dict[Union[str, int], Dict[int, OPXPlusAnalogOutputPort]] = field(
        default_factory=dict
    )
    analog_inputs: Dict[Union[str, int], Dict[int, OPXPlusAnalogInputPort]] = field(
        default_factory=dict
    )
    digital_outputs: Dict[Union[str, int], Dict[int, OPXPlusDigitalOutputPort]] = field(
        default_factory=dict
    )
    digital_inputs: Dict[Union[str, int], Dict[int, OPXPlusDigitalInputPort]] = field(
        default_factory=dict
    )

    def _get_port(
        self,
        controller_id: Union[str, int],
        port_id: int,
        port_type: str,
        create: bool = False,
        **kwargs,
    ):
        controllers = getattr(self, f"{port_type}s")

        try:
            return controllers[controller_id][port_id]
        except KeyError:
            if not create:
                raise KeyError(
                    f"Could not find existing {port_type} port: "
                    f"{port_type} ({controller_id}, {port_id}"
                )

        controllers.setdefault(controller_id, {})
        ports = controllers[controller_id]

        if port_type == "analog_output":
            ports[port_id] = OPXPlusAnalogOutputPort(controller_id, port_id, **kwargs)
        elif port_type == "analog_input":
            ports[port_id] = OPXPlusAnalogInputPort(controller_id, port_id, **kwargs)
        elif port_type == "digital_output":
            ports[port_id] = OPXPlusDigitalOutputPort(controller_id, port_id, **kwargs)
        elif port_type == "digital_input":
            ports[port_id] = OPXPlusDigitalInputPort(controller_id, port_id, **kwargs)
        else:
            raise ValueError(f"Invalid port type: {port_type}")

        return ports[port_id]

    def reference_to_port(
        self,
        port_reference: Union[QuamComponent, str],
        attr: Optional[str] = None,
        create=False,
    ) -> OPXPlusPortTypes:
        if isinstance(port_reference, QuamComponent):
            reference = port_reference.get_reference(attr=attr)
            if reference is None:
                raise ValueError("Cannot get port from reference {port_reference}")
            port_reference = reference
        elems = port_reference.split("/")
        port_type, controller_id, port_id = elems[-3:]

        port_type = port_type[:-1]
        if controller_id.isdigit():
            controller_id = int(controller_id)
        port_id = int(port_id)

        return self._get_port(controller_id, port_id, port_type, create=create)

    def get_analog_output(
        self,
        controller_id: Union[str, int],
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> OPXPlusAnalogOutputPort:
        return self._get_port(
            controller_id, port_id, port_type="analog_output", create=create, **kwargs
        )

    def get_analog_input(
        self,
        controller_id: Union[str, int],
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> OPXPlusAnalogInputPort:
        return self._get_port(
            controller_id, port_id, port_type="analog_input", create=create, **kwargs
        )

    def get_digital_output(
        self,
        controller_id: Union[str, int],
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> OPXPlusDigitalOutputPort:
        return self._get_port(
            controller_id, port_id, port_type="digital_output", create=create, **kwargs
        )

    def get_digital_input(
        self,
        controller_id: Union[str, int],
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> OPXPlusDigitalInputPort:
        return self._get_port(
            controller_id, port_id, port_type="digital_input", create=create, **kwargs
        )


@quam_dataclass
class FEMPortsContainer(QuamComponent):
    num_port_elems: ClassVar[int] = 3
    analog_outputs: Dict[
        Union[str, int], Dict[int, Dict[int, LFFEMAnalogOutputPort]]
    ] = field(default_factory=dict)
    analog_inputs: Dict[Union[str, int], Dict[int, Dict[int, LFFEMAnalogInputPort]]] = (
        field(default_factory=dict)
    )
    mw_outputs: Dict[Union[str, int], Dict[int, Dict[int, MWFEMAnalogOutputPort]]] = (
        field(default_factory=dict)
    )
    mw_inputs: Dict[Union[str, int], Dict[int, Dict[int, MWFEMAnalogInputPort]]] = (
        field(default_factory=dict)
    )
    digital_outputs: Dict[
        Union[str, int], Dict[int, Dict[int, FEMDigitalOutputPort]]
    ] = field(default_factory=dict)

    def _get_port(
        self,
        controller_id: Union[str, int],
        fem_id: int,
        port_id: int,
        port_type: str,
        create: bool = False,
        **kwargs,
    ):
        controllers = getattr(self, f"{port_type}s")

        try:
            return controllers[controller_id][fem_id][port_id]
        except KeyError:
            if not create:
                raise KeyError(
                    f"Could not find existing {port_type} port: "
                    f"{port_type} ({controller_id}, {fem_id}, {port_id}"
                )

        controllers.setdefault(controller_id, {})
        fems = controllers[controller_id]
        fems.setdefault(fem_id, {})
        ports = fems[fem_id]

        if port_type == "analog_output":
            ports[port_id] = LFFEMAnalogOutputPort(
                controller_id, fem_id, port_id, **kwargs
            )
        elif port_type == "analog_input":
            ports[port_id] = LFFEMAnalogInputPort(
                controller_id, fem_id, port_id, **kwargs
            )
        elif port_type == "mw_output":
            if "upconverter_frequency" not in kwargs and "upconverters" not in kwargs:
                kwargs["upconverter_frequency"] = 5e9
            ports[port_id] = MWFEMAnalogOutputPort(
                controller_id, fem_id, port_id, band=kwargs.get("band", 1), **kwargs
            )
        elif port_type == "mw_input":
            ports[port_id] = MWFEMAnalogInputPort(
                controller_id,
                fem_id,
                port_id,
                band=kwargs.get("band", 1),  # TODO Are default values the best here?
                downconverter_frequency=kwargs.get("downconverter_frequency", 5e9),
                **kwargs,
            )
        elif port_type == "digital_output":
            ports[port_id] = FEMDigitalOutputPort(
                controller_id, fem_id, port_id, **kwargs
            )
        else:
            raise ValueError(f"Invalid port type: {port_type}")

        return ports[port_id]

    def reference_to_port(
        self,
        port_reference: Union[QuamComponent, str],
        attr: Optional[str] = None,
        create=False,
    ) -> FEMPortTypes:
        if isinstance(port_reference, QuamBase):
            reference = port_reference.get_reference(attr=attr)
            if reference is None:
                raise ValueError("Cannot get port from reference {port_reference}")
            port_reference = reference

        elems = port_reference.split("/")
        port_type, controller_id, fem_id, port_id = elems[-4:]

        port_type = port_type[:-1]
        if controller_id.isdigit():
            controller_id = int(controller_id)
        fem_id = int(fem_id)
        port_id = int(port_id)

        return self._get_port(controller_id, fem_id, port_id, port_type, create=create)

    def get_analog_output(
        self,
        controller_id: Union[str, int],
        fem_id: int,
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> LFFEMAnalogOutputPort:
        return self._get_port(
            controller_id,
            fem_id,
            port_id,
            port_type="analog_output",
            create=create,
            **kwargs,
        )

    def get_analog_input(
        self,
        controller_id: Union[str, int],
        fem_id: int,
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> LFFEMAnalogInputPort:
        return self._get_port(
            controller_id,
            fem_id,
            port_id,
            port_type="analog_input",
            create=create,
            **kwargs,
        )

    def get_mw_output(
        self,
        controller_id: Union[str, int],
        fem_id: int,
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> MWFEMAnalogOutputPort:
        return self._get_port(
            controller_id,
            fem_id,
            port_id,
            port_type="mw_output",
            create=create,
            **kwargs,
        )

    def get_mw_input(
        self,
        controller_id: Union[str, int],
        fem_id: int,
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> MWFEMAnalogInputPort:
        return self._get_port(
            controller_id,
            fem_id,
            port_id,
            port_type="mw_input",
            create=create,
            **kwargs,
        )

    def get_digital_output(
        self,
        controller_id: Union[str, int],
        fem_id: int,
        port_id: int,
        create: bool = False,
        **kwargs,
    ) -> FEMDigitalOutputPort:
        return self._get_port(
            controller_id,
            fem_id,
            port_id,
            port_type="digital_output",
            create=create,
            **kwargs,
        )
