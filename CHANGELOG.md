## [0.1.1]
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