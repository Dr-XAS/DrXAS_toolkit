"""
Create example two-column (Energy, Mu) test files from xas_spectra.db.

Pulls two representative spectra and saves them as simple text files
in the test_data/ folder for use with identify_edge.py.

Usage:
    python create_examples.py
"""

import os
import sys
import sqlite3
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
DB_PATH = os.path.join(parent_dir, "xas_spectra.db")
OUTPUT_DIR = os.path.join(current_dir, "test_data")

# Two example spectra to extract: (element, edge, description)
EXAMPLES = [
    {"element": "Fe", "edge": "K-edge",  "filename": "Fe_K_edge.txt"},
    {"element": "Cu", "edge": "K-edge",  "filename": "Cu_K_edge.txt"},
]


def extract_spectrum(db_path, element, edge):
    """Pull one spectrum from the database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT id, element, material_name, edge, energy_json, mu_json
        FROM spectra
        WHERE download_status='success'
          AND energy_json IS NOT NULL
          AND element = ? AND edge = ?
        LIMIT 1
    """, (element, edge))

    row = c.fetchone()
    conn.close()

    if row is None:
        return None

    energy = json.loads(row['energy_json'])
    mu = json.loads(row['mu_json'])

    return {
        'id': row['id'],
        'element': row['element'],
        'name': row['material_name'],
        'edge': row['edge'],
        'energy': energy,
        'mu': mu,
    }


def save_two_column(spectrum, filepath):
    """Save spectrum as a two-column text file."""
    with open(filepath, 'w') as f:
        f.write(f"# {spectrum['element']} {spectrum['edge']} — {spectrum['name']}\n")
        f.write(f"# Source: xas_spectra.db (ID {spectrum['id']})\n")
        f.write(f"# Energy(eV)  Mu\n")
        for e, m in zip(spectrum['energy'], spectrum['mu']):
            f.write(f"{e:.4f}  {m:.6f}\n")


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for ex in EXAMPLES:
        spec = extract_spectrum(DB_PATH, ex['element'], ex['edge'])
        if spec is None:
            print(f"  WARNING: No spectrum found for {ex['element']} {ex['edge']}")
            continue

        outpath = os.path.join(OUTPUT_DIR, ex['filename'])
        save_two_column(spec, outpath)
        print(f"  Created: {outpath}")
        print(f"           {spec['element']} {spec['edge']} — {spec['name']} ({len(spec['energy'])} points)")

    print(f"\nDone. Example files are in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
