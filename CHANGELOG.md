## [Unreleased]
### Changed
- Changed `InOutIQChannel.input_offset_I/Q` to `InOutIQChannel.opx_input_offset_I/Q`

### Fixed
- Don't raise instantiation error when required_type is not a class

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