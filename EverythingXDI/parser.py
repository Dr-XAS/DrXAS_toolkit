import os
import math
import sys
import shlex

class XASParser:
    """
    Flexible parser for various XAS data formats.
    
    Supported formats:
      - Standard XDI (# Column.N: label, space-separated data)
      - CLS/BioXAS multi-event (# column N: label, comma-separated data, dual event headers)
      - Generic header-line (# energy  mu  ..., space/tab data)
      - Simple XY (2-column text: Energy Mu)
    """

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

        try:
            with open(filepath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except:
            return None, None

        if not lines:
            return None, None

        # Try parsers in order of specificity
        
        # 1. CLS multi-event format (comma-separated, dual event columns)
        energy, mu = self._parse_cls_format(lines)
        if energy and len(energy) > 5:
            return energy, mu

        # 2. Standard XDI column-defined (# Column.N: label)
        energy, mu = self._parse_xdi_columns(lines)
        if energy and len(energy) > 5:
            return energy, mu
            
        # 3. Header-line parser (# energy  i0  itrans ...)
        energy, mu = self._parse_header_line(lines)
        if energy and len(energy) > 5:
            return energy, mu

        # 4. Simple XY fallback
        energy, mu = self._parse_simple_xy(lines)
        if energy and len(energy) > 5:
            return energy, mu

        print(f"Could not parse {filepath}")
        return None, None

    # ─── Column label classification ─────────────────────────────────

    def _classify_column(self, label):
        """Classify a column label into a semantic role."""
        label = label.lower().strip()
        
        # Energy column
        if any(kw in label for kw in ['energy', 'mono']):
            # Exclude setpoints and feedback variants if we have a plain energy
            if 'fbk' in label or 'feedback' in label:
                return 'energy_fbk'
            if 'setpoint' in label or ':sp' in label:
                return 'energy_setpoint'
            if 'setting' in label:
                return 'energy_setting'
            return 'energy'
        
        # Mu / normalized
        if label in ('mu', 'xmu', 'mu(e)', 'mutrans', 'mufluor'):
            return 'mu'
        if 'norm' in label:
            return 'mu'
        
        # I0 detector
        if label in ('i0', 'i0detector', 'i0detector_darkcorrect'):
            return 'i0'
        if 'i0' in label and 'i10' not in label:
            return 'i0'
        
        # Transmission detector (I1 or itrans)
        if label in ('i1', 'itrans', 'itransmission', 'i1detector', 'i1detector_darkcorrect'):
            return 'itrans'
        if 'itrans' in label:
            return 'itrans'
        if label == 'i1' or (label.startswith('i1') and 'i10' not in label and 'i11' not in label):
            return 'itrans'
        
        # Fluorescence detector
        if any(kw in label for kw in ['fluor', 'pips', 'mca', 'idiode', 'if', 'ifluor']):
            return 'ifluor'
        
        # Reference detector
        if any(kw in label for kw in ['irefer', 'iref', 'i2']):
            return 'irefer'
            
        return 'unknown'

    def _find_data_start(self, lines, start_from=0):
        """Find the first line that looks like numeric data."""
        for i in range(start_from, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('#'):
                continue
            # Try parsing as numbers
            try:
                # Handle comma-separated
                if ',' in line:
                    parts = line.split(',')
                else:
                    parts = line.split()
                if len(parts) >= 2:
                    float(parts[0])
                    float(parts[1])
                    return i
            except (ValueError, IndexError):
                continue
        return -1

    def _compute_mu(self, parts, col_roles):
        """Compute mu from a data row given column role assignments."""
        # If we have a direct mu column, use it
        if 'mu' in col_roles:
            idx = col_roles['mu']
            if idx < len(parts):
                return float(parts[idx])
        
        # Otherwise compute from detectors
        i0_val = None
        it_val = None
        if_val = None
        
        if 'i0' in col_roles and col_roles['i0'] < len(parts):
            i0_val = float(parts[col_roles['i0']])
        if 'itrans' in col_roles and col_roles['itrans'] < len(parts):
            it_val = float(parts[col_roles['itrans']])
        if 'ifluor' in col_roles and col_roles['ifluor'] < len(parts):
            if_val = float(parts[col_roles['ifluor']])
        
        if i0_val is not None and i0_val != 0:
            if it_val is not None:
                # Transmission: mu = -ln(It/I0)
                ratio = it_val / i0_val
                if ratio > 0:
                    return -math.log(ratio)
            if if_val is not None:
                # Fluorescence: mu = If/I0  
                return if_val / i0_val
        
        return None

    # ─── CLS multi-event format ──────────────────────────────────────

    def _parse_cls_format(self, lines):
        """
        Parse CLS/BioXAS format with multi-event column definitions.
        
        Two sub-formats:
        A) '# column N: label' definitions (e.g., TMAO Arsenic file)
        B) '#(1) Event-ID "EnergySetting" "EnergyFeedback" ... "I0" "I1" ...'
           where human-readable labels are in quotes on the #(1) line.
        
        Data is always comma-separated.
        """
        # Detect CLS format
        is_cls = False
        for line in lines:
            if 'CLS Data Acquisition' in line:
                is_cls = True
                break
        
        if not is_cls:
            return None, None
        
        # Try sub-format A: "# column N: label" with Event markers
        col_defs = self._parse_cls_column_defs(lines)
        
        # Try sub-format B: "#(1) ... quoted-labels" if A didn't work
        if not col_defs:
            col_defs = self._parse_cls_parenthetical_defs(lines)
        
        if not col_defs:
            return None, None
        
        # Classify columns
        col_roles = {}
        energy_col = -1
        
        for col_num, label in col_defs.items():
            idx = col_num - 1  # Convert to 0-indexed
            role = self._classify_column(label)
            
            if role in ('energy', 'energy_fbk', 'energy_setpoint', 'energy_setting'):
                if 'energy' not in col_roles:
                    col_roles['energy'] = idx
                    energy_col = idx
            elif role == 'i0' and 'i0' not in col_roles:
                col_roles['i0'] = idx
            elif role == 'itrans' and 'itrans' not in col_roles:
                col_roles['itrans'] = idx
            elif role == 'ifluor' and 'ifluor' not in col_roles:
                col_roles['ifluor'] = idx
            elif role == 'mu' and 'mu' not in col_roles:
                col_roles['mu'] = idx
        
        if energy_col == -1:
            return None, None
        
        has_mu = 'mu' in col_roles
        has_detectors = 'i0' in col_roles and ('itrans' in col_roles or 'ifluor' in col_roles)
        if not has_mu and not has_detectors:
            return None, None
        
        # Find data start
        data_start = self._find_data_start(lines)
        if data_start == -1:
            return None, None
        
        # Parse data (comma-separated)
        energies = []
        mus = []
        
        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = [p.strip() for p in line.split(',')]
            
            try:
                if energy_col >= len(parts):
                    continue
                e_val = float(parts[energy_col])
                mu_val = self._compute_mu(parts, col_roles)
                if mu_val is not None:
                    energies.append(e_val)
                    mus.append(mu_val)
            except (ValueError, IndexError):
                continue
        
        return energies, mus

    def _parse_cls_column_defs(self, lines):
        """Parse CLS '# column N: label' definitions (sub-format A)."""
        col_defs = {}  # col_num (1-indexed) -> label
        in_event1 = False
        
        for line in lines:
            stripped = line.strip().lower()
            if '# event:' in stripped and 'readmcs' in stripped:
                in_event1 = True
                continue
            if ('# event:' in stripped and 'background' in stripped) or \
               ('# id: 2' in stripped and in_event1):
                in_event1 = False
                continue
            
            if in_event1 and stripped.startswith('#') and 'column' in stripped:
                try:
                    content = stripped.lstrip('#').strip()
                    content = content.replace('column', '').strip()
                    colon_idx = content.find(':')
                    if colon_idx != -1:
                        num_str = content[:colon_idx].strip()
                        label = content[colon_idx+1:].strip()
                        if num_str.isdigit():
                            col_defs[int(num_str)] = label
                    else:
                        parts = content.split(None, 1)
                        if len(parts) >= 2 and parts[0].isdigit():
                            col_defs[int(parts[0])] = parts[1]
                except:
                    pass
        
        return col_defs

    def _parse_cls_parenthetical_defs(self, lines):
        """
        Parse CLS '#(1)' format (sub-format B).
        
        These files have two sets of #(1) lines:
          1. PV names:   #(1) Event-ID BL1606-ID-1:Energy MONO:Energy:fbk ...
          2. Labels:     #(1) Event-ID "Energy Setting" "$(EnergyFeedback)" ... "I0" "I1" ...
        
        We use the human-readable label line (the one with quotes).
        """
        col_defs = {}
        
        # Find #(1) lines with quoted labels
        label_line = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#(1)') and '"' in stripped:
                label_line = stripped
                break
        
        if not label_line:
            # Try without quotes - use the PV-based #(1) line
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#(1)') and ':' in stripped:
                    label_line = stripped
                    break
        
        if not label_line:
            return col_defs
        
        # Parse the label line
        content = label_line[4:].strip()  # Remove '#(1)'
        
        # Try shlex to handle quotes
        try:
            labels = shlex.split(content, comments=False)
        except:
            labels = content.split()
        
        # Map to 1-indexed column numbers
        for i, label in enumerate(labels):
            col_defs[i + 1] = label.lower()
        
        return col_defs

    # ─── Standard XDI column format ──────────────────────────────────

    def _parse_xdi_columns(self, lines):
        """
        Parse standard XDI format with # Column.N: label definitions.
        Data is space-separated.
        """
        col_defs = {}  # col_num (1-indexed) -> label
        
        for line in lines:
            stripped = line.strip().lower()
            if not stripped.startswith('#'):
                continue
            
            # Match: # Column.1: energy eV   or   # column 1: energy
            content = stripped.lstrip('#').strip()
            
            # Try "Column.N:" format
            if content.startswith('column'):
                content_after = content[6:].strip()  # after "column"
                # Could be ".1:" or " 1:"
                content_after = content_after.lstrip('.')
                # Split on ':' or space
                colon_idx = content_after.find(':')
                if colon_idx != -1:
                    num_str = content_after[:colon_idx].strip()
                    label = content_after[colon_idx+1:].strip()
                else:
                    parts = content_after.split(None, 1)
                    if len(parts) >= 2:
                        num_str = parts[0]
                        label = parts[1]
                    else:
                        continue
                
                num_str = num_str.rstrip(':').strip()
                if num_str.isdigit():
                    col_defs[int(num_str)] = label
        
        if not col_defs:
            return None, None
        
        # Classify columns
        col_roles = {}
        energy_col = -1
        
        for col_num, label in col_defs.items():
            idx = col_num - 1  # 0-indexed
            role = self._classify_column(label)
            
            if role in ('energy', 'energy_fbk', 'energy_setpoint', 'energy_setting'):
                if 'energy' not in col_roles:
                    col_roles['energy'] = idx
                    energy_col = idx
            elif role == 'i0' and 'i0' not in col_roles:
                col_roles['i0'] = idx
            elif role == 'itrans' and 'itrans' not in col_roles:
                col_roles['itrans'] = idx
            elif role == 'ifluor' and 'ifluor' not in col_roles:
                col_roles['ifluor'] = idx
            elif role == 'mu' and 'mu' not in col_roles:
                col_roles['mu'] = idx
            elif role == 'irefer':
                col_roles['irefer'] = idx
        
        if energy_col == -1:
            return None, None
        
        has_mu = 'mu' in col_roles
        has_detectors = 'i0' in col_roles and ('itrans' in col_roles or 'ifluor' in col_roles)
        if not has_mu and not has_detectors:
            return None, None

        # Find data start
        data_start = self._find_data_start(lines)
        if data_start == -1:
            return None, None
        
        # Parse data (space-separated or tab-separated)
        energies = []
        mus = []
        
        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            
            try:
                if energy_col >= len(parts):
                    continue
                e_val = float(parts[energy_col])
                mu_val = self._compute_mu(parts, col_roles)
                if mu_val is not None:
                    energies.append(e_val)
                    mus.append(mu_val)
            except (ValueError, IndexError):
                continue
        
        return energies, mus

    # ─── Header-line parser ──────────────────────────────────────────

    def _parse_header_line(self, lines):
        """
        Parse files with a column-name header line like:
          #  energy  i0  itrans  irefer
        or:
          # Energy, Mu, Normalized:
        """
        header_line = ""
        data_start_idx = 0
        potential_headers = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#'):
                clean = stripped.lstrip('#').strip()
                # Heuristic: must contain "energy" (case-insensitive) and have multiple words/columns
                low = clean.lower()
                if 'energy' in low and (len(clean.split()) > 1 or ',' in clean):
                    potential_headers.append((i, clean))
            elif not stripped:
                continue
            else:
                # Reached first data line
                if potential_headers:
                    last_idx, last_content = potential_headers[-1]
                    header_line = last_content
                    data_start_idx = i
                break
        
        if not header_line:
            return None, None
        
        # Parse header columns
        # Remove trailing colons (e.g. "Energy, Mu, Normalized:")
        header_line = header_line.rstrip(':')
        
        if ',' in header_line:
            cols = [c.strip() for c in header_line.split(',')]
        else:
            try:
                cols = shlex.split(header_line, comments=False)
            except:
                cols = header_line.split()
        
        if len(cols) < 2:
            cols = header_line.replace('\t', ' ').split()
        
        # Classify columns
        col_roles = {}
        energy_col = -1
        
        for i, col_name in enumerate(cols):
            role = self._classify_column(col_name)
            if role in ('energy', 'energy_fbk', 'energy_setpoint', 'energy_setting'):
                if 'energy' not in col_roles:
                    col_roles['energy'] = i
                    energy_col = i
            elif role == 'i0' and 'i0' not in col_roles:
                col_roles['i0'] = i
            elif role == 'itrans' and 'itrans' not in col_roles:
                col_roles['itrans'] = i
            elif role == 'ifluor' and 'ifluor' not in col_roles:
                col_roles['ifluor'] = i
            elif role == 'mu' and 'mu' not in col_roles:
                col_roles['mu'] = i
        
        if energy_col == -1:
            return None, None
        
        # If we only have energy and no other roles, assume col 1 is mu
        has_mu = 'mu' in col_roles
        has_detectors = 'i0' in col_roles and ('itrans' in col_roles or 'ifluor' in col_roles)
        if not has_mu and not has_detectors:
            # Fallback: if energy is col 0, treat col 1 as mu
            if energy_col == 0 and len(cols) >= 2:
                col_roles['mu'] = 1
            else:
                return None, None
        
        # Parse data
        energies = []
        mus = []
        
        for line in lines[data_start_idx:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
            else:
                parts = line.split()
            
            if len(parts) < 2:
                continue
            
            try:
                e_val = float(parts[energy_col])
                mu_val = self._compute_mu(parts, col_roles)
                if mu_val is not None:
                    energies.append(e_val)
                    mus.append(mu_val)
            except (ValueError, IndexError):
                continue
        
        return energies, mus

    # ─── Simple XY fallback ──────────────────────────────────────────

    def _parse_simple_xy(self, lines):
        """Parses simple 2-column text files (Energy, Mu)."""
        energies = []
        mus = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    energies.append(float(parts[0]))
                    mus.append(float(parts[1]))
                except (ValueError, IndexError):
                    continue
        
        if not energies:
            return None, None
        return energies, mus
