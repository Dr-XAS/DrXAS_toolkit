import os
import sys
import math

# Add parent directory to path to import EverythingXDI
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from EverythingXDI.parser import XASParser
except ImportError:
    sys.path.append(current_dir)
    try:
        from EverythingXDI.parser import XASParser
    except ImportError:
        print("Warning: Could not import XASParser. Falling back to simple loading.")
        XASParser = None


class EdgeIdentifier:
    def __init__(self):
        # Dictionary of K-edge energies (eV)
        self.k_edges = {
            'He': 24.6, 'Li': 54.7, 'Be': 111.5, 'B': 188, 'C': 284.2, 'N': 409.9, 'O': 543.1, 'F': 696.7, 'Ne': 870.2,
            'Na': 1070.8, 'Mg': 1303, 'Al': 1559, 'Si': 1839, 'P': 2145.5, 'S': 2472, 'Cl': 2822.4, 'Ar': 3205.9,
            'K': 3608.4, 'Ca': 4038.5, 'Sc': 4492, 'Ti': 4966, 'V': 5465, 'Cr': 5989, 'Mn': 6539, 'Fe': 7112,
            'Co': 7709, 'Ni': 8333, 'Cu': 8979, 'Zn': 9659, 'Ga': 10367, 'Ge': 11103, 'As': 11867, 'Se': 12658,
            'Br': 13474, 'Kr': 14326, 'Rb': 15200, 'Sr': 16105, 'Y': 17038, 'Zr': 17998, 'Nb': 18986, 'Mo': 20000,
            'Tc': 21044, 'Ru': 22117, 'Rh': 23220, 'Pd': 24350, 'Ag': 25514, 'Cd': 26711, 'In': 27940, 'Sn': 29200,
            'Sb': 30491, 'Te': 31814, 'I': 33169, 'Xe': 34561, 'Cs': 35985, 'Ba': 37441, 'La': 38925, 'Ce': 40443,
            'Pr': 41991, 'Nd': 43569, 'Pm': 45184, 'Sm': 46834, 'Eu': 48519, 'Gd': 50239, 'Tb': 51996, 'Dy': 53789,
            'Ho': 55618, 'Er': 57486, 'Tm': 59390, 'Yb': 61332, 'Lu': 63314, 'Hf': 65351, 'Ta': 67416, 'W': 69525,
            'Re': 71676, 'Os': 73871, 'Ir': 76111, 'Pt': 78395, 'Au': 80725, 'Hg': 83102, 'Tl': 85530, 'Pb': 88005,
            'Bi': 90526, 'Po': 93105, 'At': 95730, 'Rn': 98404, 'Fr': 101137, 'Ra': 103922, 'Ac': 106755, 'Th': 109651,
            'Pa': 112601, 'U': 115606
        }

        # Dictionary of L1-edge energies (eV)
        self.l1_edges = {
            'K': 378.6, 'Ca': 438.4, 'Sc': 498, 'Ti': 564, 'V': 626, 'Cr': 696, 'Mn': 769, 'Fe': 844.6,
            'Co': 925.1, 'Ni': 1008.6, 'Cu': 1096.7, 'Zn': 1196.2, 'Ga': 1299, 'Ge': 1414.6, 'As': 1527,
            'Se': 1652, 'Br': 1782, 'Kr': 1921, 'Rb': 2065, 'Sr': 2216, 'Y': 2373, 'Zr': 2532, 'Nb': 2698,
            'Mo': 2866, 'Tc': 3043, 'Ru': 3224, 'Rh': 3412, 'Pd': 3604, 'Ag': 3806, 'Cd': 4018, 'In': 4238,
            'Sn': 4465, 'Sb': 4698, 'Te': 4939, 'I': 5188, 'Xe': 5453, 'Cs': 5714, 'Ba': 5989, 'La': 6266,
            'Ce': 6549, 'Pr': 6835, 'Nd': 7126, 'Pm': 7428, 'Sm': 7737, 'Eu': 8052, 'Gd': 8376, 'Tb': 8708,
            'Dy': 9046, 'Ho': 9394, 'Er': 9751, 'Tm': 10116, 'Yb': 10486, 'Lu': 10870, 'Hf': 11271, 'Ta': 11682,
            'W': 12100, 'Re': 12527, 'Os': 12968, 'Ir': 13419, 'Pt': 13880, 'Au': 14353, 'Hg': 14839, 'Tl': 15347,
            'Pb': 15861, 'Bi': 16388, 'Po': 16939, 'At': 17493, 'Rn': 18049, 'Fr': 18639, 'Ra': 19237,
            'Ac': 19840, 'Th': 20472, 'Pa': 21105, 'U': 21757
        }

        # Dictionary of L2-edge energies (eV)
        self.l2_edges = {
            'K': 297, 'Ca': 350, 'Sc': 403, 'Ti': 461, 'V': 521, 'Cr': 584, 'Mn': 649, 'Fe': 720,
            'Co': 794, 'Ni': 870, 'Cu': 953, 'Zn': 1044, 'Ga': 1143, 'Ge': 1248, 'As': 1359,
            'Se': 1474, 'Br': 1596, 'Kr': 1731, 'Rb': 1864, 'Sr': 2007, 'Y': 2156, 'Zr': 2307, 'Nb': 2465,
            'Mo': 2625, 'Tc': 2793, 'Ru': 2967, 'Rh': 3146, 'Pd': 3330, 'Ag': 3524, 'Cd': 3727, 'In': 3938,
            'Sn': 4156, 'Sb': 4380, 'Te': 4612, 'I': 4852, 'Xe': 5107, 'Cs': 5359, 'Ba': 5624, 'La': 5891,
            'Ce': 6164, 'Pr': 6440, 'Nd': 6722, 'Pm': 7013, 'Sm': 7312, 'Eu': 7617, 'Gd': 7930, 'Tb': 8252,
            'Dy': 8581, 'Ho': 8918, 'Er': 9264, 'Tm': 9617, 'Yb': 9978, 'Lu': 10349, 'Hf': 10739, 'Ta': 11136,
            'W': 11544, 'Re': 11959, 'Os': 12385, 'Ir': 12824, 'Pt': 13273, 'Au': 13734, 'Hg': 14209, 'Tl': 14698,
            'Pb': 15200, 'Bi': 15711, 'Po': 16244, 'At': 16785, 'Rn': 17337, 'Fr': 17907, 'Ra': 18484,
            'Ac': 19083, 'Th': 19693, 'Pa': 20314, 'U': 20948
        }

        # Dictionary of L3-edge energies (eV)
        self.l3_edges = {
             'Sc': 402, 'Ti': 456, 'V': 513, 'Cr': 575, 'Mn': 640, 'Fe': 708,
            'Co': 779, 'Ni': 855, 'Cu': 933, 'Zn': 1020, 'Ga': 1115, 'Ge': 1217, 'As': 1323, 'Se': 1436,
            'Br': 1550, 'Kr': 1675, 'Rb': 1804, 'Sr': 1941, 'Y': 2080, 'Zr': 2223, 'Nb': 2371, 'Mo': 2520,
            'Tc': 2677, 'Ru': 2838, 'Rh': 3004, 'Pd': 3173, 'Ag': 3351, 'Cd': 3538, 'In': 3730, 'Sn': 3929,
            'Sb': 4132, 'Te': 4341, 'I': 4557, 'Xe': 4782, 'Cs': 5012, 'Ba': 5247, 'La': 5483, 'Ce': 5723,
            'Pr': 5964, 'Nd': 6208, 'Pm': 6459, 'Sm': 6716, 'Eu': 6977, 'Gd': 7243, 'Tb': 7514, 'Dy': 7790,
            'Ho': 8071, 'Er': 8358, 'Tm': 8648, 'Yb': 8944, 'Lu': 9244, 'Hf': 9561, 'Ta': 9881, 'W': 10207,
            'Re': 10535, 'Os': 10871, 'Ir': 11215, 'Pt': 11564, 'Au': 11919, 'Hg': 12284, 'Tl': 12658, 'Pb': 13035,
            'Bi': 13419, 'Po': 13814, 'At': 14214, 'Rn': 14619, 'Fr': 15031, 'Ra': 15444, 'Ac': 15871, 'Th': 16300,
            'Pa': 16733, 'U': 17166
        }

    def load_spectrum(self, filepath):
        """Loads a spectrum from a file using the improved parser if available."""
        if XASParser:
            parser = XASParser()
            energy, mu = parser.parse_file(filepath)
            if energy:
                return energy, mu

        # Fallback to simple loader
        energy = []
        mu = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            energy.append(float(parts[0]))
                            mu.append(float(parts[1]))
                        except ValueError:
                            continue
            if not energy:
                return None, None
            return energy, mu
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None

    def load_spectrum_from_db(self, db_path, spectrum_id=None, element=None, edge=None, limit=None):
        """
        Load spectra directly from the xas_spectra.db SQLite database.

        Parameters
        ----------
        db_path : str
            Path to the xas_spectra.db file.
        spectrum_id : int, optional
            Specific spectrum ID to load.
        element : str, optional
            Filter by element symbol (e.g., 'Fe', 'Cu').
        edge : str, optional
            Filter by edge type (e.g., 'K-edge', 'L3-edge').
        limit : int, optional
            Maximum number of spectra to return.

        Returns
        -------
        list of dict
            Each dict has keys: id, element, edge, name, energy (list), mu (list)
        """
        import sqlite3
        import json

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        query = """SELECT id, element, material_name, edge, energy_json, mu_json
                   FROM spectra
                   WHERE download_status='success' AND energy_json IS NOT NULL"""
        params = []

        if spectrum_id is not None:
            query += " AND id = ?"
            params.append(spectrum_id)
        if element:
            query += " AND element = ?"
            params.append(element)
        if edge:
            query += " AND edge = ?"
            params.append(edge)
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = c.execute(query, tuple(params)).fetchall()
        results = []

        for row in rows:
            try:
                energy_list = json.loads(row['energy_json'])
                mu_list = json.loads(row['mu_json'])

                if energy_list and mu_list and len(energy_list) > 5:
                    results.append({
                        'id': row['id'],
                        'element': row['element'],
                        'edge': row['edge'],
                        'name': row['material_name'],
                        'energy': energy_list,
                        'mu': mu_list,
                    })
            except Exception:
                pass

        conn.close()
        return results

    def find_edge_energy(self, energy, mu):
        """Finds the edge energy by locating the maximum of the first derivative."""
        if len(energy) < 2:
            return None

        # Calculate derivative d(mu)/d(E) using simple forward difference
        derivs = []
        mid_energies = []

        for i in range(len(energy) - 1):
            de = energy[i+1] - energy[i]
            dmu = mu[i+1] - mu[i]
            if de != 0:
                derivs.append(dmu / de)
                mid_energies.append((energy[i] + energy[i+1]) / 2)
            else:
                derivs.append(0)
                mid_energies.append(energy[i])

        # Find max derivative
        max_val = -float('inf')
        max_idx = -1

        for i, val in enumerate(derivs):
            if val > max_val:
                max_val = val
                max_idx = i

        if max_idx != -1:
            return mid_energies[max_idx]
        return None

    def identify_element(self, edge_energy, tolerance=100.0):
        """Identifies the element and edge type based on the detected edge energy.

        Uses purely the derivative-determined edge energy compared against
        reference edge energies from the X-ray Data Booklet.

        Parameters
        ----------
        edge_energy : float
            The edge energy detected from the spectrum (max of 1st derivative).
        tolerance : float
            Energy window in eV to search for matches.

        Returns
        -------
        list of dict
            Sorted list of candidate matches, closest first.
        """
        if edge_energy is None:
            return []

        matches = []

        # Edge preference order for tiebreaking (K is most common)
        edge_priority = {'K': 0, 'L3': 1, 'L2': 2, 'L1': 3}

        edge_tables = {
            'K': self.k_edges,
            'L1': self.l1_edges,
            'L2': self.l2_edges,
            'L3': self.l3_edges,
        }

        for edge_name, edge_dict in edge_tables.items():
            for element, energy in edge_dict.items():
                if abs(energy - edge_energy) <= tolerance:
                    matches.append({
                        'Element': element,
                        'Edge': edge_name,
                        'Energy': energy,
                        'Diff': abs(energy - edge_energy),
                    })

        # Sort by: (1) energy difference, (2) edge priority as tiebreaker
        matches.sort(key=lambda x: (x['Diff'], edge_priority.get(x['Edge'], 9)))

        return matches


# ─── CLI helpers ─────────────────────────────────────────────────────

def process_file(identifier, filepath):
    """Process a single spectrum file."""
    energy, mu = identifier.load_spectrum(filepath)

    if energy is None:
        print(f"Skipping {os.path.basename(filepath)}: Could not load data.")
        return

    print(f"Processing file: {os.path.basename(filepath)}")

    edge_energy = identifier.find_edge_energy(energy, mu)
    if edge_energy:
        print(f"  Detected edge energy: {edge_energy:.2f} eV")

        matches = identifier.identify_element(edge_energy)

        if not matches:
            print("  No matching element found within tolerance.")
        else:
            top_match = matches[0]
            print(f"  Identified: {top_match['Element']} {top_match['Edge']}-edge (Diff: {top_match['Diff']:.2f} eV)")
    else:
        print("  Could not determine edge energy.")


def process_db(identifier, db_path, element=None, edge=None, limit=None):
    """Process spectra from the xas_spectra.db database."""
    spectra = identifier.load_spectrum_from_db(db_path, element=element, edge=edge, limit=limit)

    if not spectra:
        print("No spectra found matching criteria.")
        return

    print(f"Loaded {len(spectra)} spectra from database")
    print("=" * 80)

    for spec in spectra:
        energy = spec['energy']
        mu = spec['mu']

        edge_energy = identifier.find_edge_energy(energy, mu)

        label = f"[ID {spec['id']}] {spec['element']} - {spec['name']}"

        if edge_energy:
            matches = identifier.identify_element(edge_energy)
            if matches:
                top = matches[0]
                print(f"  {label}")
                print(f"    Detected: {edge_energy:.2f} eV -> {top['Element']} {top['Edge']}-edge (Diff: {top['Diff']:.2f} eV)")
            else:
                print(f"  {label}")
                print(f"    Detected: {edge_energy:.2f} eV -> No match")
        else:
            print(f"  {label}")
            print(f"    Could not determine edge energy")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python identify_edge.py <path_to_spectrum_file_or_directory>")
        print("  python identify_edge.py --db <path_to_db> [--element Fe] [--edge K-edge] [--limit 10]")
        sys.exit(1)

    identifier = EdgeIdentifier()

    if sys.argv[1] == '--db':
        # Database mode
        db_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(parent_dir, 'xas_spectra.db')

        element = None
        edge = None
        limit = 10

        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--element' and i + 1 < len(sys.argv):
                element = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--edge' and i + 1 < len(sys.argv):
                edge = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--limit' and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        process_db(identifier, db_path, element=element, edge=edge, limit=limit)
    else:
        # File/directory mode
        path = sys.argv[1]

        if os.path.isdir(path):
            print(f"Scanning directory: {path}")
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.startswith('.'): continue
                    if file.lower().endswith(('.dat', '.xdi', '.txt', '.001', '.002')):
                        process_file(identifier, os.path.join(root, file))
        else:
            process_file(identifier, path)


if __name__ == "__main__":
    main()
