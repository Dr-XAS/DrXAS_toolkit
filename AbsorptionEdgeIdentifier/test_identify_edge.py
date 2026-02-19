"""
Test suite for identify_edge.py using real data from the DATA directory.

Ground truth is extracted from filenames and file metadata.
Each test verifies that the identifier correctly determines the element and edge.

Usage:
    python3 AbsorptionEdgeIdentifier/test_identify_edge.py
"""

import os
import sys

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from AbsorptionEdgeIdentifier.identify_edge import EdgeIdentifier

DATA_DIR = os.path.join(parent_dir, "DATA")


# ─── Test case definitions ──────────────────────────────────────────
# Each entry: (relative_path, expected_element, expected_edge)
TEST_CASES = [
    # Standard XDI files
    ("Fe.xdi",                                          "Fe", "K"),
    ("Mn2O3.xdi",                                       "Mn", "K"),
    ("Hansel2001_greenrust_Cl_xanes_002.xdi",           "Fe", "K"),  # Green rust is an Fe compound

    # Pb foils — L1, L2, L3 edges
    ("Pb_Foil_L1_rt_2016Foils_13IDE_01.xdi",            "Pb", "L1"),
    ("Pb_Foil_L2_rt_2016Foils_13IDE_01.xdi",            "Pb", "L2"),
    ("Pb_Foil_L3_rt_2016Foils_13IDE_01.xdi",            "Pb", "L3"),

    # CLS BioXAS format (tab-separated, multi-column)
    ("Ru-Foil_2024_05_20_scan2_ideitz9q.dat",           "Ru", "K"),

    # Arsenic — standard XDI with i0/itrans/irefer columns
    ("Arsenic (III) Oxide rt_1997_04_19_scan3_idsr3103.dat",   "As", "K"),
    ("Arsenic (III) Oxide 100K_1997_04_19_scan1_id3flq8e.dat", "As", "K"),

    # CLS format — comma-separated, complex headers
    ("(CH3)3AsO(TMAO)_2019_07_03_scan13_idi4llai.dat",  "As", "K"),

    # Uranium carbonate — CLS format
    ("Ucarbonate_2010_09_02_scan1_idp8f0ne.dat",        "U",  "L3"),
    ("Ucarbonate_2010_09_02_scan3_idlu3omy.dat",        "U",  "L3"),

    # SPECTRUM_OP format (nested directory)
    ("SPECTRUM_OP_20180117_004/XAS_trans_MoFoil_300K/XAS_trans_MoFoil_300K.data.txt", "Mo", "K"),

    # RefXAS database format (space-separated, Energy Mu Normalized columns)
    ("test2/PID.SAMPLE.PREFIX2ccd9aab-32b5-447d-967c-b0e90f148cb4_metaData.txt", "Ag", "K"),
]


def run_tests():
    identifier = EdgeIdentifier()
    
    passed = 0
    failed = 0
    skipped = 0
    results = []

    print("=" * 80)
    print("AbsorptionEdgeIdentifier Test Suite")
    print("=" * 80)
    print()

    for rel_path, expected_element, expected_edge in TEST_CASES:
        filepath = os.path.join(DATA_DIR, rel_path)
        filename = os.path.basename(rel_path)
        
        # Check file exists
        if not os.path.exists(filepath):
            print(f"  SKIP  {filename}")
            print(f"         File not found: {rel_path}")
            skipped += 1
            results.append(("SKIP", filename, expected_element, expected_edge, "", "", "File not found"))
            continue

        # Load and identify
        energy, mu = identifier.load_spectrum(filepath)
        
        if energy is None or len(energy) == 0:
            print(f"  FAIL  {filename}")
            print(f"         Expected: {expected_element} {expected_edge}-edge")
            print(f"         Error: Could not parse file")
            failed += 1
            results.append(("FAIL", filename, expected_element, expected_edge, "", "", "Parse failed"))
            continue

        # Extract metadata hints for disambiguation
        element_hint, edge_hint = identifier.extract_metadata_hints(filepath)

        edge_energy = identifier.find_edge_energy(energy, mu)
        
        if edge_energy is None:
            print(f"  FAIL  {filename}")
            print(f"         Expected: {expected_element} {expected_edge}-edge")
            print(f"         Error: Could not determine edge energy")
            failed += 1
            results.append(("FAIL", filename, expected_element, expected_edge, "", "", "No edge found"))
            continue
        
        matches = identifier.identify_element(edge_energy, element_hint=element_hint, edge_hint=edge_hint)
        
        if not matches:
            print(f"  FAIL  {filename}")
            print(f"         Expected: {expected_element} {expected_edge}-edge")
            print(f"         Detected edge: {edge_energy:.2f} eV, but no match found")
            failed += 1
            results.append(("FAIL", filename, expected_element, expected_edge, f"{edge_energy:.1f}", "", "No match"))
            continue

        top_match = matches[0]
        got_element = top_match['Element']
        got_edge = top_match['Edge']
        diff = top_match['Diff']

        if got_element == expected_element and got_edge == expected_edge:
            print(f"  PASS  {filename}")
            print(f"         {expected_element} {expected_edge}-edge | Detected: {edge_energy:.2f} eV (Diff: {diff:.2f} eV)")
            passed += 1
            results.append(("PASS", filename, expected_element, expected_edge, f"{edge_energy:.1f}", f"{diff:.1f}", ""))
        else:
            # Check if expected is anywhere in the top matches
            found_in_matches = False
            for m in matches[:5]:  # Check top 5 
                if m['Element'] == expected_element and m['Edge'] == expected_edge:
                    found_in_matches = True
                    break
            
            status = "FAIL"
            note = f"Got {got_element} {got_edge}-edge instead"
            if found_in_matches:
                note += f" (correct answer in top-5)"
            
            print(f"  {status}  {filename}")
            print(f"         Expected: {expected_element} {expected_edge}-edge")
            print(f"         Got:      {got_element} {got_edge}-edge (Detected: {edge_energy:.2f} eV, Diff: {diff:.2f} eV)")
            if found_in_matches:
                print(f"         Note:    Correct answer found in top-5 matches")
            failed += 1
            results.append((status, filename, expected_element, expected_edge, f"{edge_energy:.1f}", f"{diff:.1f}", note))

    # ─── Summary ─────────────────────────────────────────────────────
    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {len(TEST_CASES)} tests")
    print("=" * 80)

    # Return exit code
    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    run_tests()
