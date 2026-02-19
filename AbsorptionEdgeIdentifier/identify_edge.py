import numpy as np
import os
import sys

class EdgeIdentifier:
    def __init__(self):
        # Dictionary of K-edge energies (eV) for elements Z=1 to Z=92 (H to U)
        # Using a subset of common XAS elements for now.
        # Data from X-ray Data Booklet (LBL)
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
        """Loads a spectrum from a file.
        Assumes first column is Energy (eV) and second is Absorption (mu).
        Skips lines starting with #.
        """
        try:
            data = np.loadtxt(filepath, comments='#')
            if data.shape[1] < 2:
                print(f"Error: File {filepath} does not have at least 2 columns.")
                return None, None
            energy = data[:, 0]
            mu = data[:, 1]
            return energy, mu
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None

    def find_edge_energy(self, energy, mu):
        """Finds the edge energy by locating the maximum of the first derivative."""
        # Calculate derivative d(mu)/d(E)
        dmu = np.gradient(mu, energy)
        
        # Find the index of the maximum derivative
        max_deriv_idx = np.argmax(dmu)
        edge_energy = energy[max_deriv_idx]
        
        return edge_energy

    def identify_element(self, edge_energy, tolerance=50.0):
        """Identifies the element and edge type based on the edge energy.
        tolerance: Energy window in eV to search for matches.
        """
        matches = []
        
        # Check K-edges
        for element, energy in self.k_edges.items():
            if abs(energy - edge_energy) <= tolerance:
                matches.append({'Element': element, 'Edge': 'K', 'Energy': energy, 'Diff': abs(energy - edge_energy)})
        
        # Check L3-edges
        for element, energy in self.l3_edges.items():
            if abs(energy - edge_energy) <= tolerance:
                matches.append({'Element': element, 'Edge': 'L3', 'Energy': energy, 'Diff': abs(energy - edge_energy)})
        
        # Sort by difference
        matches.sort(key=lambda x: x['Diff'])
        
        return matches

def main():
    if len(sys.argv) < 2:
        print("Usage: python identify_edge.py <path_to_spectrum_file>")
        sys.exit(1)
        
    filepath = sys.argv[1]
    
    identifier = EdgeIdentifier()
    energy, mu = identifier.load_spectrum(filepath)
    
    if energy is None:
        sys.exit(1)
        
    print(f"Processing file: {filepath}")
    
    edge_energy = identifier.find_edge_energy(energy, mu)
    print(f"Detected edge energy (max derivative): {edge_energy:.2f} eV")
    
    matches = identifier.identify_element(edge_energy)
    
    if not matches:
        print("No matching element found within tolerance.")
    else:
        print("\nPossible matches:")
        for match in matches:
            print(f"  {match['Element']} {match['Edge']}-edge (Standard: {match['Energy']:.1f} eV, Diff: {match['Diff']:.2f} eV)")
            
        top_match = matches[0]
        print(f"\nidentified: {top_match['Element']} {top_match['Edge']}-edge")

if __name__ == "__main__":
    main()
