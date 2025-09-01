## [0.4.2]

### Added

- Added `duration` and `fidelity` as optional parameters to `QuamMacro`

### Fixed

- Fixed `QuamBase.get_attr_name()` failing when an attribute was a reference.
- Fixed arbitrary waveforms on IQ/MW channels not converting Q component to list consistently
- Changed default `time_of_flight` from 24 ns to 140 ns to fix error on newer qm-qua versions
  - 140 ns seems like a reasonable default for most channels
- Fixed type annotation issue in `QuamRoot.load()` method causing linting errors for subclasses like `BasicQuam`
- Fixed `Pulse.waveform_function` return type being wrong
- Compatibility with qm-qua 1.2.3: Updated channel measure command to explicitly pass `adc_stream`
- Removed all private imports from `qm.qua`
- Fixed float-to-int coercion during component instantiation

## [0.4.0]

### Added

- Add support for qubit-level components and gate implementations
  - Add `QuantumComponent` and subclasses `Qubit` and `QubitPair`.
    These introduce qubit-level objects to interfacce with circuit-level languages.
  - Add qubit-level macros (`BaseMacro`, `QuamMacro`, `QubitMacro`, `QubitPairMacro`, `PulseMacro`) that implementations for gate operations.
  - Add `OperationsRegistry` to register gate-level operations.
  - See documentation for details.
- Add `Channel.reset_if_phase()` which matches the QUA command `reset_if_phase(element)`
- Add the QUAM config, which can be called from the terminal command `quam config`.
  This enables adding a default QUAM state path
- Add config entry `raise_error_missing_reference` to raise error if a reference is missing, rather than a warning
- Add the following properties to the `JSONSerialiser`: `content_mapping`, `include_defaults`, and `state_path`.
- Add `quam.__version__`

### Changed

- `JSONSerialiser.content_mapping` structure has been changed from dict `{filename.json: [list of components]}` to `{component: filname.json}`. The previous format is still supported although this raises a warning
- Remove implicit support for content mapping structure `{filename.json: component} (note the lack of a list). This used to be supported even though it was never mentioned.
- The default state path for a `QuamRoot` is now retrieved from the environment variable `QUAM_STATE_PATH`, and if this doesn't exist, from the quam config.
- Add `__class__` to serialisation (`to_dict` method), even if the target class matches the expected type
- If a specific class can't be imported during instantiation, a warning will be raised and it will load the default class (specified by the type hint) instead
- QuAM has been renamed to QUAM
  - Some root classes have been renamed to CamelCase (e.g. `BasicQuAM` -> `BasicQuam`)
- Deprecate Quam component method`get_unreferenced_value` in favor of naming `get_raw_value`

## [0.3.10]

### Changed

- `QuamBase.generate_config()` now returns a `DictQuaConfig` instead of a `Dict[str, Any]`
  This provides type hints for the generated config.
- Add `MWFEMAnalogInputPort.gain_db` to allow for setting the gain of the analog input port
- Removed warning when multiple QuamRoot objects are instantiated
- Added `SingleChannel.exponential_filter` in compliance with QOP 3.3.
- Deprecated `SingleChannel.filter_iir_taps` in favor of `SingleChannel.exponential_filter` for the LF-FEM

### Fixed

- Fixed `QuamBase.iterate_components()` arg `skip_elems` having the wrongtype
- Deprecated `thread` argument in favor of `core` in `Channel` when qm >= 1.2.2
- Fixed `MWFEMAnalogOutputPort.upconverters` not being converted to a dict in the config
- Fixed QUA type import errors due to qm-qua 1.2.2 changing type locations

## [0.3.9]

### Added

- Added `QuamBase.set_at_reference` to set a value at a reference
- Added `string_reference.get_parent_reference` to get the parent reference of a string reference
- Added `FrequencyConverter.LO_frequency` setter which updates the local oscillator frequency
- Added optional `relative_path` to method `QuamBase.get_reference()`
- Added support for multiple QuamRoot objects
- Added `QuamBase.get_root()` to get the QuamRoot object of a component

### Changed

- `Pulse.integration_weights` now defaults to `#./default_integration_weights`, which returns [(1, pulse.length)]

### Fixed

- Fixed issues with parameters being references in a QuamRoot object
- Fixed `MWFEMAnalogOutputPort.upconverters` not having the correct type
- A warning is raised if a new `QuamRoot` instance is created while a previous one exists.
- Fixed `MWFEMAnalogOutputPort.upconverters` not being converted to a dict in the config
- Fixed: Improve error message when instantiating: list or dict expected but a different type is provided
- `MWChannel.upconverter_frequency` and `MWChannel.LO_frequency` now correctly return the upconverter frequency from the `opx_output` port, supporting both `upconverter_frequency` and `upconverters` specifications.

## [0.3.8]

### Added

- Added time tagging to channels
- Added support for Python 3.12

### Removed

- Removed support for Python 3.8
- Added `Pulse.play()` method

### Fixed

- Change location of port feedforward and feedback filters in config
- Convert port crosstalk to dict in config, fixing deepcopy issues

## [0.3.7]

### Added

- Added `WaveformPulse` to allow for pre-defined waveforms.

## [0.3.6]

### Changed

- Modified `MWChannel` to also have `RF_frequency` and `LO_frequency` to match the signature of `IQChannel`.
  This is done by letting both inherit from a new base class `_OutComplexChannel`.

## [0.3.5]

### Added

- Added `DragCosinePulse`.
- Added support for sticky channels through the `StickyChannelAddon` (see documentation)
- Added `Channel.thread`, which defaults to None
- QUAM can now be installed through PyPi

### Changed

- Aded ports for different hardware. As a consequence we now also support the LF-FEM and MW-FEM
- `Channel` is now an abstract base class.
- Moved `intermediate_frequency` to `Channel` from `SingleChannel/IQChannel`.
  The default is `None`. A consequence of this is that `SingleChannel` no longer adds
  `intermediate_frequency` to the config if it's not set.

## [0.3.4]

### Added

- Added `Channel.frame_rotation_2pi` to allow for frame rotation in multiples of 2pi
- Added `Channel.update_frequency` to allow for updating the frequency of a channel
- Added `OctaveOld.connectivity` as it was needed for (deprecated) compatibility with multiple OPX instruments

### Changed

- Allow `QuamBase.get_reference(attr)` to return a reference of one of its attributes
- Octave RF input 2 has `LO_source = "external"` by default
- Rename `DragPulse -> DragGaussianPulse`, deprecate `DragPulse`

### Fixed

- Fix quam object instantiation error when a parameter type uses pipe operator
- Allow int keys to be serialised / loaded in QuAM using JSONSerialiser
- Fix type `OctaveUpconverter.triggered_reersed` -> `OctaveUpconverter.triggered_reversed`
- Fix tuples not being instantiated properly in specific circumstances
- Fix filter_fir/iir_taps being passed as QuamList when generating config, resulting in an error due to parent reassignment
- Fix warning messages in QuamComponent instantiation

## [0.3.3]

### Added

- Added the following parameters to `IQChannel`: `RF_frequency`, `LO_frequency`, `intermediate_frequency`
- Added the following properties to `IQChannel`: `inferred_RF_frequency`, `inferred_LO_frequency`, `inferred_intermediate_frequency`
  These properties can be attached to the relevant parameters to infer the frequency from the remaining two parameters.
- Added `IQChannel.inferred_RF/LO/intermediate_frequency`
  These can be used to infer the frequency from the remaining two frequencies

### Changed

- Deprecated the `rf_frequency` property in favor of the `RF_frequency` parameter in `IQChannel`
- Added channel types: `InSingleChannel`, `InIQChannel`, `InSingleOutIQChannel`, `InIQOutSingleChannel`
- Restructured channels to allow for other channel types.
- `IQChannel` now has all three frequency parameters: `RF_frequency`, `LO_frequency`, `intermediate_frequency`
- Deprecated `IQChannel.rf_frequency` in favor of `IQChannel.RF_frequency`

### Fixed

- Fixed dataclass ClassVar parameters being wrongly classified as optional or required dataclass args
- Made `ConstantReadoutPulse` a dataclass, and removed some wrong docstring

## [0.3.2]

### Added

- Added full QuAM documentation, including web hosting
- Added `BasicQuAM` to QuAM components

### Fixed

- Fix error where a numpy array of integration weights raises an error
- Fix instantiation of a dictionary where the value is a reference
- Fix optional parameters of a quam component parent class were sometimes categorized as a required parameter (ReadoutPulse)

## [0.3.1]

### Added

- Add optional `config_settings` property to quam components indicating that they should be called before/after other components when generating QUA configuration
- Added `InOutIQChannel.measure_accumulated/sliced`
- Added `ReadoutPulse`. All readout pulses can now be created simply by inheriting from the `ReadoutPulse` and the non-readout variant.
- Added `Channel.set_dc_offset`

### Changed

- Pulses with `pulse.axis_angle = None` are now compatible with an `IQChannel` as all signal on the I port.

### Fixed

- Switched channel `RF_inputs` and `RF_outputs` for Octave
- Loading QuAM components when the expected type is a union or the actual type is a list
  no longer raises an error
- The qua config entries from OctaveUpConverter entries I/Q_connection were of type
  QuamList, resulting in errors during deepcopy. Converted to tuple

## [0.3.0]

### Added

- Added InOutSingleChannel
- Added optional `config_settings` property to quam components indicating that they should be called before/after other components when generating QUA configuration
- Added support for the new Octave API.
- Added support for `Literal` types in QuAM

### Changed

- Changed `InOutIQChannel.input_offset_I/Q` to `InOutIQChannel.opx_input_offset_I/Q`
- Renamed `SingleChannel.output_offset` -> `SingleChannel.opx_output_offset`
- Pulse behaviour modifications to allow pulses to be attached to objects other than channels. Changes conist of following components
  - Added `pulse.channel`, which returns None if both its parent & grandparent is not a `Channel`
  - Rename `Pulse.full_name` -> `Pulse.name`.
    Raises error if `Pulse.channel` is None
    TODO Check if this causes issues
  - `Pulse.apply_to_config` does nothing if pulse has no channel
- Raise AttributeError if channel doesn't have a well-defined name.
  This happens if channel.id is not set, and channel.parent does not have a name either
- `Pulse.axis_angle` is now in radians instead of degrees.
- Channel offsets (e.g. `SingleChannel.opx_output_offset`) is None by default (see note in Fixed)
- Move `quam.components.superconducting_qubits` to `quam.examples.superconducting_qubits`
- Replaced `InOutIQChannel.measure` kwargs `I_var` and `Q_var` by `qua_vars` tuple
- `Pulse.id` is now an instance variable instead of a class variable
- Channel frequency converter default types are now `BaseFrequencyConverter` which has fewer attributes than `FrequencyConverter`. This is to make it compatible with the new Octave API.

### Fixed

- Don't raise instantiation error when required_type is not a class
- Add support for QuAM component sublist type: List[List[...]]
- Channel offsets (e.g. `SingleChannel.opx_output_offset`) are ensured to be unique, otherwise a warning is raised
  - Previously the offset could be overwritten when two channels share the same port
  - Default values are None, and they're only added if nonzero
  - If the offset is not specified in config at the end, it's manually added to be 0.0
- JSON serializer doesn't break if an item is added to ignore that isn't part of QuAM
- Allow `QuamDict` keys to be integers

## [0.2.2] -

### Added

- Overwriting a reference now raises an error. A referencing attribute must first be set to None

## [0.2.1] -

This release primarily targets Octave compatibility

### Changes

- `FrequencyConverter` and `LocalOscillator` both have a method `configure()` added
- Improve documentation of `IQChannel`, `InOutIQChannel`
- Various fixes to Octave, including removal of any code specific to a single QuAM setup
- Allow `expected_type` in `instantiate_attrs` to be overridden when `__class__` is provided.
- Remove `_value_annotation` when calling `get_dataclass_attr_annotation`
- Slightly expanded error message in `validate_obj_type`

## [0.2.0] -

### Changed

- Quam components now user `@quam_dataclass` decorator instead of `@dataclass(kw_only=True)`

## [0.1.1] -

Only registering changes from November 29th

### Added

- Add `Pulse.axis_angle` for most pulses that specifies axis on IQ plane if defined
- Add `validate` kwarg to `pulse.play()`
- Add `InOutIQChannel.measure()`
- Add `ArbitraryWeightsReadoutPulse`

### Changed

- `InOutIQChannel.frequency_converter_down` default is None
- Change `ConstantReadoutPulse` -> `ConstantWeightsReadoutPulse`

### Fixed
