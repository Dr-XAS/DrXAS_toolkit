# DrXAS Toolkit

This repository contains a collection of toolkits for the Dr-XAS project.

## Toolkits

### AbsorptionEdgeIdentifier

A tool to identify the element and absorption edge from a given XAS spectrum.

#### Usage

1. Place your XAS spectrum data file (text format, columns: Energy, Mu) in the `AbsorptionEdgeIdentifier/test_data` directory (or anywhere else).
2. Run the identification script:

    ```bash
    python3 AbsorptionEdgeIdentifier/identify_edge.py <path_to_your_file>
    ```

    Example:

    ```bash
    python3 AbsorptionEdgeIdentifier/identify_edge.py AbsorptionEdgeIdentifier/test_data/sample_Fe_K_edge.txt
    ```

#### Features

* Detects edge energy using the maximum of the first derivative.
* Identifies the element and edge (K or L3) by comparing with standard values.
* Pure Python implementation (no external dependencies required).
