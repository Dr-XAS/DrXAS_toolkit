import math
import os

def generate_spectrum(filename, edge_energy, step_height=1.0, width=5.0):
    """Generates a synthetic XAS spectrum without numpy."""
    try:
        # Create energy range
        energy = []
        start_e = edge_energy - 50
        end_e = edge_energy + 100
        steps = 300
        step_size = (end_e - start_e) / steps
        for i in range(steps):
            energy.append(start_e + i * step_size)
    
        mu = []
        peak_center = edge_energy + 2.0
        peak_sigma = 2.0
        peak_amp = 0.5 * step_height
    
        for e in energy:
            # Arctan step
            step = step_height * (0.5 + (1/math.pi) * math.atan((e - edge_energy) / (width/2)))
        
            # Gaussian peak
            peak = peak_amp * math.exp(-0.5 * ((e - peak_center) / peak_sigma)**2)
        
            val = step + peak
            mu.append(val)
    
        # Save to file
        with open(filename, 'w') as f:
            f.write('# Energy(eV)  Mu(E)\n')
            for e, m in zip(energy, mu):
                f.write(f'{e:.4f}  {m:.4f}\n')
        
        print(f"Generated {filename} with edge at {edge_energy} eV")
    except Exception as e:
        print(f"Error generating data: {e}")

if __name__ == "__main__":
    output_dir = 'AbsorptionEdgeIdentifier/test_data'
    filepath = os.path.join(output_dir, 'sample_Fe_K_edge.txt')
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    generate_spectrum(filepath, 7112.0)
