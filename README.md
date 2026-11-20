<p align="center">
  <img src="extras/icon.svg" alt="Project screenshot">
</p>

# MNeuEventGUI

MNeuEventLib is an event data filtering library for ISIS Neutron and Muon Source.

It is a GUI frontend for [MNeuEventLib](https://github.com/ISISMuon/MNeuEventLib).

It is currently a work in progress, and some API features are missing. It was originally
written as the GUI component of [MuonDataLib](https://github.com/ISISMuon/MuonDataLib).

## Installation
### Prebuilt executables
Check the [releases](https://github.com/ISISMuon/MNeuEventGUI/releases/) tab for prebuilt executables for Windows and MacOS.

### From source
MNeuEventGUI can be installed from source using `pip`:
```bash
pip install .
```

It can then be run as an executable module:
```bash
python3 -m MNeuEventGUI
```

It is also possible to directly run the package from source via [`uvx`](https://docs.astral.sh/uv/guides/tools/). Simply
download the repository and then run in the repository root
```bash
uvx .
```
