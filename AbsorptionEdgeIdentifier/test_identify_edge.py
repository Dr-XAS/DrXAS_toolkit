"""
Test suite for identify_edge.py using spectra from xas_spectra.db.

Loads spectra directly from the SQLite database — no file parsing needed.
Ground truth comes from the database's element and edge columns.

Usage:
    python3 AbsorptionEdgeIdentifier/test_identify_edge.py
"""

import os
import sys
import sqlite3
import json

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from AbsorptionEdgeIdentifier.identify_edge import EdgeIdentifier

DB_PATH = os.path.join(parent_dir, "xas_spectra.db")


def normalize_edge(edge_str):
    """Normalize edge labels from DB to standard form: K, L1, L2, L3."""
    if not edge_str:
        return None
    e = edge_str.strip()
    # Handle "K-edge", "L3-edge" etc.
    if e.endswith('-edge'):
        return e.replace('-edge', '').upper()
    # Handle dict-format: "{'K': 7112}"
    if e.startswith('{'):
        try:
            d = eval(e)  # Safe: controlled DB content
            if isinstance(d, dict):
                return list(d.keys())[0].upper()
        except:
            pass
    return e.upper()


def get_test_spectra(db_path, per_element_edge=1):
    """
    Pull a representative set of spectra from the database for testing.
    
    Selects `per_element_edge` spectra for each unique (element, edge) combination
    that has a clean edge label (K-edge, L1-edge, L2-edge, L3-edge).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all unique (element, edge) pairs with clean labels
    c.execute("""
        SELECT DISTINCT element, edge 
        FROM spectra 
        WHERE download_status='success' 
          AND energy_json IS NOT NULL 
          AND edge IN ('K-edge', 'L1-edge', 'L2-edge', 'L3-edge')
        ORDER BY element, edge
    """)
    pairs = [(r['element'], r['edge']) for r in c.fetchall()]
    
    test_spectra = []
    
    for element, edge in pairs:
        c.execute("""
            SELECT id, element, material_name, edge, energy_json, mu_json
            FROM spectra
            WHERE download_status='success'
              AND energy_json IS NOT NULL
              AND element = ? AND edge = ?
            LIMIT ?
        """, (element, edge, per_element_edge))
        
        for row in c.fetchall():
            try:
                energy = json.loads(row['energy_json'])
                mu = json.loads(row['mu_json'])
                if energy and mu and len(energy) > 10:
                    test_spectra.append({
                        'id': row['id'],
                        'element': row['element'],
                        'edge': edge,
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
    test_spectra = get_test_spectra(DB_PATH, per_element_edge=1)
    
    passed = 0
    failed = 0
    errors = 0
    fail_details = []
    
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
            continue
        
        # Use element/edge from DB as hints (same as real usage)
        matches = identifier.identify_element(
            edge_energy,
            element_hint=expected_element,
            edge_hint=expected_edge
        )
        
        if not matches:
            failed += 1
            fail_details.append((spec['id'], expected_element, expected_edge, edge_energy, "No match", ""))
            continue
        
        top = matches[0]
        got_element = top['Element']
        got_edge = top['Edge']
        
        if got_element == expected_element and got_edge == expected_edge:
            passed += 1
        else:
            failed += 1
            fail_details.append((
                spec['id'], expected_element, expected_edge, edge_energy,
                f"{got_element} {got_edge}", f"{top['Diff']:.1f}"
            ))
    
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
    
    # Exit with appropriate code
    if accuracy >= 80:
        print(f"Test suite PASSED (accuracy >= 80%)")
        sys.exit(0)
    else:
        print(f"Test suite FAILED (accuracy < 80%)")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
