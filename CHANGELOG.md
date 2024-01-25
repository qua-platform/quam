
## [Unreleased]
### Added
- Added InOutSingleChannel
- Add optional `config_settings` property to quam components indicating that they should be called before/after other components when generating QUA configuration

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