---
name: add-fem-support
description: Use when adding support for a new OPX1000 FEM (Front-End Module) type to quam — e.g. a new qm-qua-sdk PR introduces a FEM type like LF/MW/BB and quam needs matching port classes, container wiring, and tests. Also use when asked "how do I add FEM X support" or when touching quam/components/ports/ for a new fem_type.
---

# Adding a new FEM type to quam

quam mirrors qm-qua-sdk's OPX1000 FEM port types as its own dataclasses. Adding
a new FEM type (the way BB-FEM was added, see qm-labs/qm-qua-sdk#1234) means
touching the same handful of files every time. This skill is the checklist.

## 0. Research the qm-qua-sdk source first

Find the qm-qua-sdk PR/commit that introduces the FEM type. You need, from
`qm/config/_ports/` in that SDK:

- `_port_base.py`: the new `Fem` subclass (e.g. `class BbFem(Fem): ...`) — just
  a marker class, no fields.
- `_analog_output.py` / `_analog_input.py`: the new port classes (e.g.
  `AnalogOutputPortBaseband`). Compare field-by-field against the existing
  LF-FEM port class to see what's added/removed (BB-FEM, for example, is LF-FEM
  minus `output_mode` — no "amplified" mode).
- `_digital_output.py` / `_digital_input.py`: usually the new FEM reuses the
  existing digital port shape unchanged — check before assuming you need a new
  digital port class.
- `qm/type_hinting/config_types.py`: the `Literal["XX"]` string that goes into
  `config["controllers"][id]["fems"][n]["type"]`. This exact string is what
  quam's `fem_type: ClassVar[str]` must match.

Don't guess these from memory — pull the actual PR diff (`gh pr view <N> --repo
qm-labs/qm-qua-sdk --json files,body`, then `gh api
repos/qm-labs/qm-qua-sdk/pulls/<N>/files -q '.[] | select(.filename=="...") |
.patch'`) since dual-use fields and defaults are easy to get subtly wrong.

## 1. quam's FEM architecture (read this once, applies to every FEM type)

- `quam/components/ports/base_ports.py`: `FEMPort(BasePort, ABC)` is the shared
  base. `fem_type: ClassVar[str]` is the discriminator. `get_port_config()`
  writes `fem_cfg["type"] = self.fem_type` into the generated config dict and
  raises if an FEM slot already has a conflicting type. **No FEM-specific logic
  lives here** — this file never needs editing to add a new FEM type.
- `quam/components/ports/analog_outputs.py` / `analog_inputs.py`: one class per
  FEM type per direction, e.g. `LFFEMAnalogOutputPort(LFAnalogOutputPort,
  FEMPort)`, `MWFEMAnalogOutputPort(FEMPort)`. Each sets `fem_type: ClassVar[str]`
  and implements `get_port_properties()` returning the plain dict that goes
  into the config (never anything FEM-specific in `base_ports.py`).
- `quam/components/ports/digital_outputs.py`: `FEMDigitalOutputPort` has **no**
  `fem_type` override — it's reused by every FEM type as-is, unless the new
  FEM's digital port schema genuinely differs (check step 0).
- `quam/components/ports/ports_containers.py`: `FEMPortsContainer` has one dict
  field per `(fem, direction)` pair (`analog_outputs`/`analog_inputs` for LF,
  `mw_outputs`/`mw_inputs` for MW, `bb_outputs`/`bb_inputs` for BB — **not** a
  single generic dict), a `_get_port()` if/elif dispatcher keyed by a
  `port_type` string, and `get_<x>_output`/`get_<x>_input` public methods.
  `FEMPortTypes` is the `Union[...]` of every concrete port class.
- `quam/components/channels.py` only references concrete port classes (e.g.
  `LFFEMAnalogOutputPort`) for the *default tuple-construction convenience*
  (`opx_output=("con1", 1, 2)` implicitly builds an LF port). A new FEM type
  does **not** need changes here — users instantiate the new port class
  explicitly, the same way `MWFEMAnalogOutputPort` already requires explicit
  construction (no tuple shorthand).

## 2. Implementation checklist

1. **`quam/components/ports/analog_outputs.py`**: add `<XX>FEMAnalogOutputPort`
   mirroring the closest existing class (usually `LFFEMAnalogOutputPort`),
   dropping/adding fields per step 0's diff. Add to `__all__`.
2. **`quam/components/ports/analog_inputs.py`**: same for
   `<XX>FEMAnalogInputPort`. Add to `__all__`.
3. **Digital ports**: only touch `digital_outputs.py`/`digital_inputs.py` if
   step 0 showed a genuinely different schema. Otherwise skip — `FEMDigitalOutputPort`
   already covers it.
4. **`quam/components/ports/ports_containers.py`**:
   - import the two new port classes
   - add them to the `FEMPortTypes` union
   - add `<xx>_outputs`/`<xx>_inputs` dict fields to `FEMPortsContainer`
   - add `"<xx>_output"`/`"<xx>_input"` to the valid-`port_type` set in `_get_port`
   - add the dispatch branches in `_get_port` (mirror the `mw_output`/`mw_input`
     branches — inject sane defaults into `kwargs` first if the new port type
     has required fields, like MW's `band`/`upconverter_frequency` defaults)
   - add `get_<xx>_output`/`get_<xx>_input` public methods
5. **Unit tests**: new file
   `tests/components/ports/test_<xx>_fem_analog_ports.py`, mirroring
   `test_lf_fem_analog_ports.py` (plain-dict assertions: constructor arg
   validation via `pytest.raises(TypeError)`, default property values,
   `to_dict(include_defaults=False)`, `get_port_properties()`, and
   `apply_to_config()` producing `{"controllers": {"con1": {"fems": {1:
   {"type": "<XX>", ...}}}}}`). Also extend
   `tests/components/ports/test_ports_containers.py`'s parametrized
   `test_fem_ports_container_add_ports` / `..._reference_to_port` lists and
   `port_mapping` dicts with the new `<xx>_output`/`<xx>_input` cases, plus the
   `test_fem_ports_container_initialize` assertion.
6. **CHANGELOG.md**: one line under `### Added` in `[Unreleased]`.

## 3. The two things worth doing beyond the obvious

### Validate against qm-qua's real schema, not just plain-dict assertions

The plain-dict tests above only check that quam's output has the shape you
*intended*. They don't catch drift against what `qm-qua` actually accepts.
There's a second, stronger layer:

```python
from qm import QuantumMachinesManager
from qm.program._qua_config_schema import load_config

QuantumMachinesManager.set_capabilities_offline()  # no QOP server/simulator needed

config = machine.generate_config()
load_config(config)  # raises ConfigSchemaError if qm-qua's real schema rejects it
```

This runs in plain `pytest` — no cloud secrets, no local QOP, no simulator —
and is a much stronger check than the plain-dict tests. Add your new FEM's case
to `tests/components/ports/test_fem_qm_qua_schema_validation.py` alongside the
existing LF/MW/OPX+ cases.

**The new FEM type almost certainly isn't in the currently-pinned `qm-qua`
yet.** Mark the new test `xfail(raises=ConfigSchemaError, strict=False,
reason="...names the qm-qua-sdk PR and the qm-qua version that will ship
it...")`. `strict=False` means it silently flips to `XPASS` (not a failure)
once `qm-qua` is upgraded — at that point delete the `xfail` marker to make it
a real assertion. Don't bump `pyproject.toml`'s `qm-qua` pin until the real
release ships (not an rc/pre-release) — verify locally first (see below), but
leave the dependency constraint alone so CI keeps testing what's actually
released.

To verify locally before the real release: `pip install
"qm-qua==<the-pre-release-version>"` directly into the venv (don't add it to
`pyproject.toml`/commit a lockfile change), rerun the test, confirm it
genuinely `XPASS`es, then revert the install. This is how BB-FEM's schema test
was proven correct against `qm-qua==1.5.0rc2` before the dependency was
touched.

This same schema-validation harness also tends to surface *unrelated*
pre-existing bugs (e.g. it caught that `DigitalOutputChannel` omitted
`delay`/`buffer` from `digitalInputs` config when unset, which `qm-qua`'s
schema requires unconditionally). Fix those for real — they're genuine bugs,
not FEM-specific — in their own commit/PR, separate from the new-FEM work.

### Also extend the cloud-simulator suite (secondary, secrets-gated)

`tests_against_simulator/test_config_validity/` does real `qmm.open_qm()`
against a cloud/local QOP simulator (see its `conftest.py`). It's excluded from
default `pytest` runs (`testpaths = ["tests"]`) and only runs in CI's gated
`simulator` job. Add `make_<xx>_output_port`/`make_<xx>_input_port` helpers to
its `conftest.py` and a couple of parametrized cases to `test_channels.py`,
again `xfail(strict=False)` until the simulator/qm-qua supports it. This is
weaker signal than the offline schema check (needs secrets/a simulator to even
run) but catches things schema validation can't (actual program compilation).

