# EverythingXDI

A toolkit for converting various XAS data formats into standard XAS .xdi formats and parsing them.

## Components

### Parser

`parser.py` contains the `XASParser` class which can parse different file formats to extract Energy and Absorption (Mu) data.

#### Supported formats

- **Standard XDI**: Files with standard XDI headers.
- **CLS/BioXAS**: Files with column definitions in comments (e.g., `# Column.1: Energy`).
- **Simple XY**: Files with two columns (Energy, Mu).

#### Usage

```python
from EverythingXDI.parser import XASParser

parser = XASParser()
energy, mu = parser.parse_file("path/to/file.dat")

if energy:
    print(f"Loaded {len(energy)} points.")
else:
    print("Failed to parse file.")
```
