# QuAM Installation

## :one: Pre-requisites

/// tab | For Windows
- Windows 10 (build 1809 and later), or Windows 11
- 3.8 ≤ Python ≤ 3.11, we recommend Python 3.10 or 3.11
    <!-- For Python 3.8 and 3.9, please see additional notes (TODO add note reference) -->
- [Git version control system](https://git-scm.com/), or a Git GUI such as [GitHub Desktop](https://desktop.github.com/) or [GitKraken](https://www.gitkraken.com/)

/// details | Using a virtual environment
    type: tip

It is recommended to install QuAM in a Python virtual environment.

If using Anaconda, this can be done via

```bash
conda create -n {environment_name}  
conda activate {environment_name}
```

Be sure to replace `{environment_name}` with a name of your choosing

To create a virtual environment without Anaconda, open PowerShell :octicons-terminal-16:, navigate to
a folder where you would like to create a virtual environment, and execute the 
following command:

```
python -m venv {environment_name}  
source {environment_name}\Scripts\Activate.ps1
```
///
///

/// tab | For MacOS
- Tested on MacOS Ventura and MacOS Sonoma
- Python 3.9 or higher, we recommend Python 3.10 or higher
- [Git version control system](https://git-scm.com/), or a Git GUI such as [GitHub Desktop](https://desktop.github.com/) or [GitKraken](https://www.gitkraken.com/)

/// details | Using a virtual environment
    type: tip

It is recommended to install QuAM in a Python virtual environment.  
To create a virtual environment, open terminal :octicons-terminal-16:, navigate to a folder where you would like to create a virtual environment, and execute the following command:
```
python -m venv {environment_name}
source {environment_name}/bin/activate
```
///
///

/// tab | For Linux
- QuAM has not been tested on Linux. However, it should follow similar instructions as MacOS.
///

## :two: Installation
QuAM can be installed directly using `pip` or by cloning the repository from GitHub.

### Pip installation (recommended)

The easiest way to install QuAM is directly using `pip`:

```bash
pip install git+https://github.com/qua-platform/quam.git
```

### Developer installation from Git

Alternatively, The QuAM repository can be downloaded using Git. Open Powershell / terminal :octicons-terminal-16: in a desired installation folder and run the following command:
```bash
git clone https://github.com/qua-platform/quam.git
pip3 install ./quam
```
/// details | Installation from a Git GUI
    type: note

If you're not using Git directly but a Git client, please clone the repository from <https://github.com/qua-platform/quam.git>.  
Then open Powershell / terminal :octicons-terminal-16:, navigate to the downloaded folder `quam` and run

```
pip3 install .
```
///

/// details | Error message "command not found: pip3"
    type: warning

In case the error message `command not found: pip3` is displayed, try using the alternative command
```
pip install ./quam
```
If this raises a similar error, it likely means that Python cannot be found. Please check that you have Python installed. If you've set up a virtual environment, please ensure that it has been activated (see `Pre-requisites`).
///

## :three: Next Steps

QuAM comes with a range of standard QuAM components that can kick-start experimental setups. An example of these components are used can be found at the [QuAM demonstration](demonstration.md).

Beyond the standard components, QuAM provides a framework to create custom components that are tailored to a specific quantum setup. This allows you to create their own abstraction layers, enabling you to digitally represent and interact with your quantum setup. See [Creating custom QuAM components](/components/custom-components) for details

<!-- ### Overview of components
#### quam.components.hardware
- Mixer
- LocalOscillator

#### quam.components.channels
- Channel
- SingleChannel
- IQChannel
- InOutIQChannel

#### quam.components.pulses
- Pulse
- ReadoutPulse
- ConstantReadoutPulse
- DragPulse
- SquarePulse
- GaussianPulse -->