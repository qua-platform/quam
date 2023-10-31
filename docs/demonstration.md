# QuAM demonstration

In this demonstration we will create a basic superconducting setup using standard components. 
Note that QuAM is not specific to superconducting setups but is meant to serve any quantum platform.

The standard QuAM components can be imported using

```python
from quam.components import *
```

Since we're starting from scratch, we will have to instantiate all QuAM components. This has to be done once, after which we will generally save and load QuAM from a file.
To begin, we create the top-level QuAM object, which inherits from [quam.core.quam_classes.QuamRoot][]. Generally the user is encouraged to create a custom component for this.

We will call our top-level object `machine`:
```python
machine = superconducting_qubits.QuAM()
```

So far, this object `machine` is empty, so we'll populate it with objects.
In this case, we will create two Transmon objects and fill them with contents. 


/// details | Autocomplete with IDEs
    type: tip
Code editors with Python language support (e.g., VS Code, PyCharm) are very useful here because they explain what attributes each class has, what the type should be, and docstrings. This makes it a breeze to create a QuAM from scratch.
///


```python
num_qubits = 2
for idx in range(num_qubits):
    # Create qubit components
    transmon = superconducting_qubits.Transmon(
        id=idx,
        xy=IQChannel(
            local_oscillator=LocalOscillator(power=10, frequency=6e9),
            mixer=Mixer(),
            output_port_I=("con1", 3 * idx + 3),
            output_port_Q=("con1", 3 * idx + 4),
        ),
        z=SingleChannel(output_port=("con1", 3 * idx + 5)),
    )
    machine.qubits.append(transmon)

    # Create resonator components
    resonator = InOutIQChannel(
        input_port_I=("con1", 1),
        input_port_Q=("con1", 2),
        output_port_I=("con1", 1),
        output_port_Q=("con1", 2),
        id=idx, 
        local_oscillator=LocalOscillator(power=10, frequency=6e9),
        mixer=Mixer()
    )
    machine.resonators.append(resonator)
```
This example demonstrates that QuAM follows a tree structure: each component can have a parent and it can have children as attributes.


## Saving and loading QuAM

Now that we have defined our QuAM structure, we can save its contents to a JSON file:

```python
machine.save("state.json")
```

/// details | state.json
```json
{
    "qubits": [
        {
            "id": 0,
            "xy": {
                "output_port_I": [
                    "con1",
                    3
                ],
                "output_port_Q": [
                    "con1",
                    4
                ],
                "mixer": {},
                "local_oscillator": {
                    "frequency": 6000000000.0,
                    "power": 10
                }
            },
            "z": {
                "output_port": [
                    "con1",
                    5
                ]
            }
        },
        {
            "id": 1,
            "xy": {
                "output_port_I": [
                    "con1",
                    6
                ],
                "output_port_Q": [
                    "con1",
                    7
                ],
                "mixer": {},
                "local_oscillator": {
                    "frequency": 6000000000.0,
                    "power": 10
                }
            },
            "z": {
                "output_port": [
                    "con1",
                    8
                ]
            }
        }
    ],
    "resonators": [
        {
            "id": 0,
            "output_port_I": [
                "con1",
                1
            ],
            "output_port_Q": [
                "con1",
                2
            ],
            "mixer": {},
            "local_oscillator": {
                "frequency": 6000000000.0,
                "power": 10
            },
            "input_port_I": [
                "con1",
                1
            ],
            "input_port_Q": [
                "con1",
                2
            ]
        },
        {
            "id": 1,
            "output_port_I": [
                "con1",
                1
            ],
            "output_port_Q": [
                "con1",
                2
            ],
            "mixer": {},
            "local_oscillator": {
                "frequency": 6000000000.0,
                "power": 10
            },
            "input_port_I": [
                "con1",
                1
            ],
            "input_port_Q": [
                "con1",
                2
            ]
        }
    ],
    "__class__": "quam.components.superconducting_qubits.QuAM"
}
```
///

This JSON file is a serialised representation of QuAM. As a result, QuAM can also be loaded from this JSON file:

```python
loaded_quam = QuAM.load("state.json")
```

## Generating the QUA configuration

We can also generate the QUA config from QuAM. This recursively calls `QuamComponent.apply_to_config()` on all QuAM components.

```python
qua_config = machine.generate_config()
```

/// details | qua_config
```json
{
  "version": 1,
  "controllers": {
    "con1": {
      "analog_outputs": {
        "3": {
          "offset": 0
        },
        "4": {
          "offset": 0
        },
        "5": {
          "offset": 0
        },
        "6": {
          "offset": 0
        },
        "7": {
          "offset": 0
        },
        "8": {
          "offset": 0
        },
        "1": {
          "offset": 0
        },
        "2": {
          "offset": 0
        }
      },
      "digital_outputs": {},
      "analog_inputs": {
        "1": {
          "offset": 0
        },
        "2": {
          "offset": 0
        }
      }
    }
  },
  "elements": {
    "q0.xy": {
      "mixInputs": {
        "I": [
          "con1",
          3
        ],
        "Q": [
          "con1",
          4
        ],
        "lo_frequency": 6000000000.0,
        "mixer": "q0.xy.mixer"
      },
      "intermediate_frequency": 0.0,
      "operations": {}
    },
    "q0.z": {
      "singleInput": {
        "port": [
          "con1",
          5
        ]
      },
      "operations": {}
    },
    "q1.xy": {
      "mixInputs": {
        "I": [
          "con1",
          6
        ],
        "Q": [
          "con1",
          7
        ],
        "lo_frequency": 6000000000.0,
        "mixer": "q1.xy.mixer"
      },
      "intermediate_frequency": 0.0,
      "operations": {}
    },
    "q1.z": {
      "singleInput": {
        "port": [
          "con1",
          8
        ]
      },
      "operations": {}
    },
    "IQ0": {
      "mixInputs": {
        "I": [
          "con1",
          1
        ],
        "Q": [
          "con1",
          2
        ],
        "lo_frequency": 6000000000.0,
        "mixer": "IQ0.mixer"
      },
      "intermediate_frequency": 0.0,
      "operations": {},
      "outputs": {
        "out1": [
          "con1",
          1
        ],
        "out2": [
          "con1",
          2
        ]
      },
      "smearing": 0,
      "time_of_flight": 24
    },
    "IQ1": {
      "mixInputs": {
        "I": [
          "con1",
          1
        ],
        "Q": [
          "con1",
          2
        ],
        "lo_frequency": 6000000000.0,
        "mixer": "IQ1.mixer"
      },
      "intermediate_frequency": 0.0,
      "operations": {},
      "outputs": {
        "out1": [
          "con1",
          1
        ],
        "out2": [
          "con1",
          2
        ]
      },
      "smearing": 0,
      "time_of_flight": 24
    }
  },
  "pulses": {
    "const_pulse": {
      "operation": "control",
      "length": 1000,
      "waveforms": {
        "I": "const_wf",
        "Q": "zero_wf"
      }
    }
  },
  "waveforms": {
    "zero_wf": {
      "type": "constant",
      "sample": 0.0
    },
    "const_wf": {
      "type": "constant",
      "sample": 0.1
    }
  },
  "digital_waveforms": {
    "ON": {
      "samples": [
        [
          1,
          0
        ]
      ]
    }
  },
  "integration_weights": {},
  "mixers": {
    "q0.xy.mixer": [
      {
        "intermediate_frequency": 0.0,
        "lo_frequency": 6000000000.0,
        "correction": [
          1.0,
          0.0,
          0.0,
          1.0
        ]
      }
    ],
    "q1.xy.mixer": [
      {
        "intermediate_frequency": 0.0,
        "lo_frequency": 6000000000.0,
        "correction": [
          1.0,
          0.0,
          0.0,
          1.0
        ]
      }
    ],
    "IQ0.mixer": [
      {
        "intermediate_frequency": 0.0,
        "lo_frequency": 6000000000.0,
        "correction": [
          1.0,
          0.0,
          0.0,
          1.0
        ]
      }
    ],
    "IQ1.mixer": [
      {
        "intermediate_frequency": 0.0,
        "lo_frequency": 6000000000.0,
        "correction": [
          1.0,
          0.0,
          0.0,
          1.0
        ]
      }
    ]
  },
  "oscillators": {}
}
```
///

This QUA config can then be used in QUA to open a Quantum Machine:
```python
qm = qmm.open_qm(qua_config)  # opens a quantum machine with configuration
```