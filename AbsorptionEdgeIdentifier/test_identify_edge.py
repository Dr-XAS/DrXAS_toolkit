"""
Test suite for identify_edge.py using spectra from xas_spectra.db.

Loads spectra directly from the SQLite database — no file parsing needed.
Ground truth comes from the database's element and edge columns.
Plots all tested spectra as subplots with identification results.

Usage:
    python3 AbsorptionEdgeIdentifier/test_identify_edge.py
"""

import os
import sys
import sqlite3
import json
import math

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from AbsorptionEdgeIdentifier.identify_edge import EdgeIdentifier

DB_PATH = os.path.join(parent_dir, "xas_spectra.db")

N_SAMPLES = 50  # Number of random spectra to test


def normalize_edge(edge_str):
    """Normalize edge labels from DB to standard form: K, L1, L2, L3."""
    if not edge_str:
        return None
    e = edge_str.strip()
    if e.endswith('-edge'):
        return e.replace('-edge', '').upper()
    if e.startswith('{'):
        try:
            d = eval(e)
            if isinstance(d, dict):
                return list(d.keys())[0].upper()
        except:
            pass
    return e.upper()


def get_test_spectra(db_path, n_samples=N_SAMPLES):
    """
    Randomly sample `n_samples` spectra from the database for testing.
    Only selects spectra with clean edge labels (K-edge, L1-edge, L2-edge, L3-edge).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT id, element, material_name, edge, energy_json, mu_json
        FROM spectra
        WHERE download_status='success'
          AND energy_json IS NOT NULL
          AND edge IN ('K-edge', 'L1-edge', 'L2-edge', 'L3-edge')
        ORDER BY RANDOM()
    """)
    rows = c.fetchall()

    test_spectra = []
    for row in rows:
        if len(test_spectra) >= n_samples:
            break
        try:
            energy = json.loads(row['energy_json'])
            mu = json.loads(row['mu_json'])
            if energy and mu and len(energy) > 10:
                test_spectra.append({
                    'id': row['id'],
                    'element': row['element'],
                    'edge': row['edge'],
                    'name': row['material_name'],
                    'energy': energy,
                    'mu': mu,
                })
        except:
            pass

    conn.close()
    return test_spectra


def run_tests():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    identifier = EdgeIdentifier()
    test_spectra = get_test_spectra(DB_PATH, n_samples=N_SAMPLES)

    passed = 0
    failed = 0
    errors = 0
    fail_details = []
    plot_data = []  # Collect results for plotting

    print("=" * 90)
    print(f"AbsorptionEdgeIdentifier Test Suite — xas_spectra.db ({len(test_spectra)} spectra)")
    print("=" * 90)
    print()

    for spec in test_spectra:
        expected_element = spec['element']
        expected_edge = normalize_edge(spec['edge'])

        if expected_edge is None:
            continue

        energy = spec['energy']
        mu = spec['mu']

        # Detect edge
        edge_energy = identifier.find_edge_energy(energy, mu)

        if edge_energy is None:
            errors += 1
            plot_data.append({
                'energy': energy, 'mu': mu,
                'expected': f"{expected_element} {expected_edge}",
                'got': "ERROR", 'edge_energy': None, 'is_pass': False,
            })
            continue

        # Identify purely from derivative — no metadata hints
        matches = identifier.identify_element(edge_energy)

        if not matches:
            failed += 1
            fail_details.append((spec['id'], expected_element, expected_edge, edge_energy, "No match", ""))
            plot_data.append({
                'energy': energy, 'mu': mu,
                'expected': f"{expected_element} {expected_edge}",
                'got': "No match", 'edge_energy': edge_energy, 'is_pass': False,
            })
            continue

        top = matches[0]
        got_element = top['Element']
        got_edge = top['Edge']
        is_pass = (got_element == expected_element and got_edge == expected_edge)

        if is_pass:
            passed += 1
        else:
            failed += 1
            fail_details.append((
                spec['id'], expected_element, expected_edge, edge_energy,
                f"{got_element} {got_edge}", f"{top['Diff']:.1f}"
            ))

        plot_data.append({
            'energy': energy, 'mu': mu,
            'expected': f"{expected_element} {expected_edge}",
            'got': f"{got_element} {got_edge}",
            'edge_energy': edge_energy,
            'is_pass': is_pass,
        })

    # ─── Results ─────────────────────────────────────────────────────
    total = passed + failed + errors
    accuracy = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    print(f"  PASSED:   {passed}")
    print(f"  FAILED:   {failed}")
    print(f"  ERRORS:   {errors} (could not detect edge energy)")
    print(f"  TOTAL:    {total}")
    print(f"  ACCURACY: {accuracy:.1f}%")
    print()

    if fail_details:
        print("─── Failed cases ───")
        print(f"  {'ID':>6}  {'Expected':>12}  {'Got':>12}  {'Edge eV':>10}  {'Diff':>6}")
        print(f"  {'─'*6}  {'─'*12}  {'─'*12}  {'─'*10}  {'─'*6}")
        for spec_id, exp_el, exp_edge, e_ev, got, diff in fail_details[:30]:
            print(f"  {spec_id:>6}  {exp_el + ' ' + exp_edge:>12}  {got:>12}  {e_ev:>10.2f}  {diff:>6}")
        if len(fail_details) > 30:
            print(f"  ... and {len(fail_details) - 30} more")

    print()
    print("=" * 90)

    # ─── Plot all tested spectra ─────────────────────────────────────
    try:
        import matplotlib.pyplot as plt

        n = len(plot_data)
        ncols = 5
        nrows = math.ceil(n / ncols)

        fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows))
        fig.suptitle(
            f"Edge Identification Test — {passed}/{total} correct ({accuracy:.0f}%)",
            fontsize=14, fontweight='bold'
        )

        # Flatten axes for easy indexing
        if nrows == 1:
            axes = [axes] if ncols == 1 else list(axes)
        else:
            axes = [ax for row in axes for ax in row]

        for i, entry in enumerate(plot_data):
            ax = axes[i]
            e = entry['energy']
            m = entry['mu']

            color = '#2196F3' if entry['is_pass'] else '#F44336'
            ax.plot(e, m, color=color, linewidth=0.8)

            # Mark detected edge energy with a vertical line
            if entry['edge_energy'] is not None:
                ax.axvline(entry['edge_energy'], color='#FF9800', linewidth=1, linestyle='--', alpha=0.8)

            # Title: expected vs got
            if entry['is_pass']:
                title = f"✓ {entry['expected']}"
            else:
                title = f"✗ {entry['expected']}\n→ {entry['got']}"

            ax.set_title(title, fontsize=7, color='green' if entry['is_pass'] else 'red')
            ax.tick_params(labelsize=6)
            ax.set_xlabel('Energy (eV)', fontsize=6)
            ax.set_ylabel('μ(E)', fontsize=6)

        # Hide unused subplots
        for j in range(n, len(axes)):
            axes[j].set_visible(False)

        plt.tight_layout()
        plt.show()

    except ImportError:
        print("matplotlib not available — skipping plot.")

    # Exit with appropriate code
    if accuracy >= 60:
        print(f"Test suite PASSED (accuracy >= 60%)")
        sys.exit(0)
    else:
        print(f"Test suite FAILED (accuracy < 60%)")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
