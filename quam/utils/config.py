__all__ = ["generate_config_final_actions"]


def generate_config_final_actions(qua_config):
    """Performs final actions on the generated qua config.

    This is called at the end of `QuamRoot.generate_config()`.
    In this case it ensures that all analog outputs and inputs have a defined offset

    Args:
        qua_config (dict): The generated qua config.
    """
    for controller_cfg in qua_config["controllers"].values():
        if "fems" in controller_cfg:
            for fem in controller_cfg["fems"].values():
                if fem.get("type") == "LF":
                    if "analog_outputs" in fem:
                        for analog_output in fem["analog_outputs"].values():
                            analog_output.setdefault("offset", 0.0)
                    if "analog_inputs" in fem:
                        for analog_input in fem["analog_inputs"].values():
                            analog_input.setdefault("offset", 0.0)

        if "analog_outputs" in controller_cfg:
            for analog_output in controller_cfg["analog_outputs"].values():
                analog_output.setdefault("offset", 0.0)
        if "analog_inputs" in controller_cfg:
            for analog_input in controller_cfg["analog_inputs"].values():
                analog_input.setdefault("offset", 0.0)
