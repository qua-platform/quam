from quam.utils.config import generate_config_final_actions


def test_config_no_overwrite_existing_offset():
    cfg = {
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.5}},
                "analog_inputs": {2: {"offset": 0.5}},
            },
        },
    }

    generate_config_final_actions(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.5}},
                "analog_inputs": {2: {"offset": 0.5}},
            },
        },
    }


def test_config_default_offset():
    cfg = {
        "controllers": {
            "con1": {
                "analog_outputs": {1: {}},
                "analog_inputs": {2: {}},
            },
        },
    }

    generate_config_final_actions(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.0}},
                "analog_inputs": {2: {"offset": 0.0}},
            },
        },
    }


def test_config_default_offset_LF_FEM():
    cfg = {
        "controllers": {
            "con1": {
                "fems": {
                    2: {
                        "type": "LF",
                        "analog_outputs": {1: {}},
                        "analog_inputs": {2: {}},
                    },
                },
            },
        },
    }

    generate_config_final_actions(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "fems": {
                    2: {
                        "type": "LF",
                        "analog_outputs": {1: {"offset": 0.0}},
                        "analog_inputs": {2: {"offset": 0.0}},
                    },
                },
            },
        },
    }


def test_config_no_overwrite_existing_offset_LF_FEM():
    cfg = {
        "controllers": {
            "con1": {
                "fems": {
                    2: {
                        "type": "LF",
                        "analog_outputs": {1: {"offset": 0.5}},
                        "analog_inputs": {2: {"offset": 0.5}},
                    },
                },
            },
        },
    }

    generate_config_final_actions(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "fems": {
                    2: {
                        "type": "LF",
                        "analog_outputs": {1: {"offset": 0.5}},
                        "analog_inputs": {2: {"offset": 0.5}},
                    },
                },
            },
        },
    }


def test_config_default_offset_no_outputs_inputs_entries():
    cfg = {"controllers": {"con1": {}}}

    generate_config_final_actions(cfg)

    assert cfg == {"controllers": {"con1": {}}}


def test_config_default_offset_no_outputs_inputs():
    cfg = {
        "controllers": {
            "con1": {
                "analog_outputs": {},
                "analog_inputs": {},
            }
        }
    }

    generate_config_final_actions(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "analog_outputs": {},
                "analog_inputs": {},
            }
        }
    }
