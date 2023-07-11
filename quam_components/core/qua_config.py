from .quam_element import QuamElement


qua_config_template = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {},
            "digital_outputs": {},
            "analog_inputs": {},
        }
    },
    "elements": {},
    "pulses": {},
    "waveforms": {},
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
    "integration_weights": {},
    "mixers": {}
}


def build_config(quam, qua_config=None):
    if qua_config is None:
        qua_config = qua_config_template.copy()

    for val in quam.values():
        if isinstance(val, dict):
            build_config(quam=val, qua_config=qua_config)
        elif isinstance(val, list):
            for elem in val:
                build_config(quam=elem, qua_config=qua_config)
        elif isinstance(val, QuamElement):
            val.apply_to_config(config=qua_config)

    return qua_config
