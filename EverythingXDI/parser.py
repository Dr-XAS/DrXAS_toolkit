import os
import math
import sys
import shlex

class XASParser:
    def __init__(self):
        pass

    def parse_file(self, filepath):
        """
        Parses a file to extract Energy and Mu.
        Returns (energy_list, mu_list) or (None, None) if failed.
        """
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return None, None

        # Try specific parsers
        
        # 1. Try generic column-defined parser (common in CLS/BioXAS data)
        energy, mu = self.parse_column_defined(filepath)
        if energy and len(energy) > 0:
            return energy, mu
            
        # 2. Try header-line generic parser (e.g. lines starting with # Energy Mu ...)
        energy, mu = self.parse_header_line(filepath)
        if energy and len(energy) > 0:
            return energy, mu

        # 3. Simple XY parser (fallback)
        energy, mu = self.parse_simple_xy(filepath)
        if energy and len(energy) > 0:
            return energy, mu

        print(f"Could not parse {filepath}")
        return None, None

    def parse_column_defined(self, filepath):
        """
        Parses files where metadata defines columns like '# column 1: Energy'
        """
        col_map = {}
        data_start_line = 0
        
        try:
            with open(filepath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except:
            return None, None
            
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for column definitions
            # Match formats like "# column 1: label" or "# Column.1: label"
            if line.startswith('#'):
                # Normalize line
                l_lower = line.lower()
                if 'column' in l_lower:
                    try:
                        # simple parsing
                        parts = l_lower.replace(':', ' ').replace('.', ' ').split()
                        # find index of 'column'
                        col_idx = -1
                        if 'column' in parts:
                            idx_scanner = parts.index('column') + 1
                            if idx_scanner < len(parts):
                                num_str = parts[idx_scanner].rstrip(':')
                                if num_str.isdigit():
                                    col_num = int(num_str) - 1 # 0-indexed
                                    # Rest of the line is label
                                    label = l_lower
                                    col_map[col_num] = label
                    except:
                        pass
            else:
                if not line: continue
                # First non-comment line is usually data start (if not preceded by a specific header line)
                # But sometimes there are empty lines. 
                # Let's assume data starts when we see numbers.
                try:
                    # check if line contains numbers
                    if any(c.isdigit() for c in line):
                        # check if it splits into floats
                        [float(x) for x in line.split(',')[0].split()]
                        data_start_line = i
                        break
                except:
                    continue

        if not col_map:
            return None, None

        # Identify Energy and Mu columns
        energy_col = -1
        i0_col = -1
        i1_col = -1 # Trans
        if_col = -1 # Fluor (pips, diode, etc.)
        mu_col = -1 # Direct mu

        for c, label in col_map.items():
            if 'energy' in label and 'fbk' not in label and 'setpoint' not in label: 
                # Prefer achieved energy or just 'energy'
                if energy_col == -1: energy_col = c
            elif 'energy' in label:
                # Fallback to setpoint/fbk if no main energy found, but keep looking
                 if energy_col == -1: energy_col = c
            
            if 'i0' in label: i0_col = c
            if 'i1' in label and 'i10' not in label: i1_col = c
            if 'i2' in label: pass
            if 'fluor' in label or 'pips' in label or 'mca' in label or 'idiode' in label:
                if if_col == -1: if_col = c
            
            if ('mu' in label and 'multi' not in label) or 'norm' in label:
                mu_col = c

        # If we have explicit header definition in the file that maps to column numbers like the first file example
        # The first file: "# column 2: $(EnergyFeedback)..."
        # The logic above tries to catch this.

        if energy_col == -1:
            # Fallback: look for Energy in first few mapped columns
            for c, label in col_map.items():
                if 'energy' in label: energy_col = c; break
        
        if energy_col == -1: return None, None

        # Extract data
        energies = []
        mus = []

        for line in lines[data_start_line:]:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            # Handle comma or space delimiter
            if ',' in line: parts = line.split(',')
            else: parts = line.split()
            
            try:
                # Check bounds
                if energy_col >= len(parts): continue
                
                e_val = float(parts[energy_col])
                
                mu_val = 0.0
                if mu_col != -1 and mu_col < len(parts):
                    mu_val = float(parts[mu_col])
                else:
                    # Calculate mu
                    i0_val = 1.0
                    if i0_col != -1 and i0_col < len(parts):
                       i0_val = float(parts[i0_col])
                    
                    # Prevent div by zero
                    if i0_val == 0: i0_val = 1e-9

                    if i1_col != -1 and i1_col < len(parts): # Trasmission
                        i1_val = float(parts[i1_col])
                        if i1_val <= 0: i1_val = 1e-9
                        mu_val = -math.log(i1_val / i0_val)
                    elif if_col != -1 and if_col < len(parts): # Fluorescence
                        if_val = float(parts[if_col])
                        mu_val = if_val / i0_val
                    elif i0_col != -1 and i1_col == -1 and if_col == -1:
                         # Maybe i0 is actually total count and we don't have reference? Unlikely in XAS.
                         # Assume transmission if only i0 and one other large detector exist?
                         pass
                    else:
                        # Can't calculate mu
                        return None, None
                
                energies.append(e_val)
                mus.append(mu_val)
            except ValueError:
                continue
                
        return energies, mus

    def parse_header_line(self, filepath):
        """
        Parses files with a single header line starting with #
        """
        try:
            with open(filepath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except:
             return None, None
             
        header_line = ""
        data_start_idx = 0
        
        # Look for last comment line that has "Energy"
        # Scan from bottom up or top down? Top down to header, then data follows.
        
        potential_headers = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#'):
                clean_line = line.lstrip('#').strip()
                # Heuristic: must contain Energy and at least 3 words
                if ('Energy' in clean_line or 'energy' in clean_line) and len(clean_line.split()) > 2:
                    potential_headers.append((i, clean_line))
            elif not line:
                continue
            else:
                # Reached data (non-comment line)
                if potential_headers:
                    # Use the last header found before data
                    last_idx, last_content = potential_headers[-1]
                    header_line = last_content
                    data_start_idx = i
                break
                
        if not header_line: return None, None
        
        # Use shlex to handle quotes
        try:
             # shlex.split(s, comments=False) is safer if # is in the header content
            cols = shlex.split(header_line, comments=False)
        except:
            cols = header_line.split()
            
        if len(cols) < 2: 
            # try splitting by tab or multiple spaces
             cols = header_line.replace('\t', ' ').split()

        # Map columns
        col_map = {i: c.lower() for i, c in enumerate(cols)}
        
        energy_col = -1
        mu_col = -1
        i0_col = -1
        i1_col = -1
        if_col = -1
        
        for i, label in col_map.items():
            if 'energy' in label and energy_col == -1: energy_col = i
            if ('mu' in label or 'norm' in label) and mu_col == -1: mu_col = i
            if 'i0' in label: i0_col = i
            if 'i1' in label: i1_col = i
            if 'pips' in label or 'fluor' in label or 'idiode' in label: if_col = i
            
        if energy_col == -1: return None, None
        
        energies = []
        mus = []
        
        for line in lines[data_start_idx:]:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            # Use shlex or simple split for data? Data usually doesn't have quotes.
            # But comma separation might exist.
            if ',' in line: parts = line.split(',')
            else: parts = line.split()
            
            if len(parts) < 2: continue
            
            try:
                # Handle potential quoting in data (unlikely but possible)
                e_val = float(parts[energy_col])
                mu_val = 0.0
                
                if mu_col != -1 and mu_col < len(parts):
                    mu_val = float(parts[mu_col])
                else:
                    i0_val = 1.0
                    if i0_col != -1 and i0_col < len(parts): i0_val = float(parts[i0_col])
                    if i0_val == 0: i0_val = 1e-9
                    
                    if i1_col != -1 and i1_col < len(parts):
                        i1_val = float(parts[i1_col])
                        if i1_val <= 0: i1_val = 1e-9
                        mu_val = -math.log(i1_val / i0_val)
                    elif if_col != -1 and if_col < len(parts):
                        if_val = float(parts[if_col])
                        mu_val = if_val / i0_val
                    else:
                         return None, None
                            
                energies.append(e_val)
                mus.append(mu_val)
            except:
                continue
                
        return energies, mus

    def parse_simple_xy(self, filepath):
        """
        Parses simple 2-column text files (Energy, Mu)
        """
        energies = []
        mus = []
        try:
             with open(filepath, 'r', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            energies.append(float(parts[0]))
                            mus.append(float(parts[1]))
                        except: continue
        except:
             return None, None
             
        if not energies: return None, None
        return energies, mus
