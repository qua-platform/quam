# Octave

An Octave is represented in QuAM through the [quam.components.octave.Octave][] class.


## Creating the Octave
Below we show how an Octave is instantiated using some example arguments:

```python
from quam.components.octave import Octave, OctaveUpConverter, OctaveDownConverter

octave = Octave(
    name="octave1",
    ip="127.0.0.1",
    port=80,
)
```

We can next retrieve the Octave config `QmOctaveConfig`, used to create the `QuantumMachinesManager`
```python
octave_config = octave.get_octave_config()
# The calibration_db and device_info are automatically configured

qmm = QuantumMachinesManager(host={opx_host}, port={opx_port}, octave=octave_config)
```

At this point the channel connectivity of the Octave hasn't yet been configured.
We can do so by adding frequency converters.

### Adding frequency converters
A frequency converter is a grouping of the components needed to upconvert or downconvert a signal.
These typically consist of a local oscillator, mixer, as well as IF, LO, and RF ports.
For the Octave we have two types of frequency converters:

- [OctaveUpConverter][quam.components.octave.OctaveUpConverter]: Used to upconvert a pair of IF signals to an RF signal
- [OctaveDownCovnerter][quam.components.octave.OctaveDownConverter]: Used to downconvert an RF signal to a pair of IF signals

When the Octave is connected to a single OPX in the default connectivity (for details see [OPX-Octave Connectivity](https://docs.quantum-machines.co/1.1.7/qm-qua-sdk/docs/Guides/octave/#opx-octave-connectivity)), initializing the frequency converters is very straightforward:

```python
octave.initialize_default_connectivity()

octave.print_summary()
```


## Combined example
```python
from quam.components.octave import Octave, OctaveUpConverter, OctaveDownConverter

octave = Octave(
    name="octave1",
    ip="127.0.0.1",
    port=80,
)

octave.initialize_default_connectivity()

octave.print_summary()
```