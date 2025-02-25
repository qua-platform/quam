__all__ = ["generate_config_final_actions"]


def generate_config_final_actions(qua_config):
    """Performs final actions on the generated qua config.

    This is called at the end of `QuamRoot.generate_config()`.
    In this case it ensures that all analog outputs and inputs have a defined offset

    Args:
        qua_config (dict): The generated qua config.
    """
    # Add default dc offset 0V to all analog outputs and inputs if not set
    for controller_cfg in qua_config["controllers"].values():
        for fem in controller_cfg.get("fems", {}).values():
            if fem.get("type") != "LF":
                continue
            for analog_output in fem.get("analog_outputs", {}).values():
                analog_output.setdefault("offset", 0.0)
            for analog_input in fem.get("analog_inputs", {}).values():
                analog_input.setdefault("offset", 0.0)

        if "analog_outputs" in controller_cfg:
            for analog_output in controller_cfg["analog_outputs"].values():
                analog_output.setdefault("offset", 0.0)
        if "analog_inputs" in controller_cfg:
            for analog_input in controller_cfg["analog_inputs"].values():
                analog_input.setdefault("offset", 0.0)
