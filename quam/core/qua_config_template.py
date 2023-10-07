qua_config_template = {
    "version": 1,
    "controllers": {},
    "elements": {},
    "pulses": {
        "const_pulse": {
            "operation": "control",
            "length": 1000,
            "waveforms": {"I": "const_wf", "Q": "zero_wf"},
        }
    },
    "waveforms": {
        "zero_wf": {"type": "constant", "sample": 0.0},
        "const_wf": {"type": "constant", "sample": 0.1},
    },
    "digital_waveforms": {
        "ON": {"samples": [[1, 0]]}
    },  # TODO Technically this waveform isn't used
    "integration_weights": {},
    "mixers": {},
    "oscillators": {},
}
