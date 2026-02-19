import os
import sys

# Add parent directory to path to import EverythingXDI
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from EverythingXDI.parser import XASParser
except ImportError:
    # Fallback if running from root
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
                # print(f"Error: No valid data found in {filepath} (fallback loader).")
                return None, None
            return energy, mu
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None

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
        """Identifies the element and edge type based on the edge energy.
        tolerance: Energy window in eV to search for matches.
        """
        if edge_energy is None:
            return []
            
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

def process_file(identifier, filepath):
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python identify_edge.py <path_to_spectrum_file_or_directory>")
        sys.exit(1)
        
    path = sys.argv[1]
    identifier = EdgeIdentifier()
    
    if os.path.isdir(path):
        print(f"Scanning directory: {path}")
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.startswith('.'): continue
                # Basic extension check
                if file.lower().endswith(('.dat', '.xdi', '.txt', '.001', '.002')):
                    process_file(identifier, os.path.join(root, file))
    else:
        process_file(identifier, path)

if __name__ == "__main__":
    main()
