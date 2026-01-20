#!/usr/bin/env python3
"""Fix apostrophe issues in the cleaned manuscript"""

import re
from pathlib import Path

from project_paths import DOCS_DIR

def fix_apostrophes(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix incorrect —s back to 's
    content = content.replace('—s', "'s")
    content = content.replace('—t', "'t")
    content = content.replace('—d', "'d")
    content = content.replace('—re', "'re")
    content = content.replace('—ll', "'ll")
    content = content.replace('—ve', "'ve")
    content = content.replace('—m', "'m")
    
    # Fix the escalation of force procedures - convert to list
    eof_pattern = r'Escalation of force procedures for convoy turret gunners: 150 meters—give hand and arm signals to the oncoming vehicle 100 meters—shoot a pen flare oblique to the vehicle 75 meters—use the M16 service rifle, fire warning shots at the road and oblique 50 meters—switch to the mounted turret gun, fire disabling shots into the vehicle—s grill, hood, and engine block 25 meters—fire kill shots into the driver—s windshield'
    
    eof_replacement = '''Escalation of force procedures for convoy turret gunners:

- 150 meters—give hand and arm signals to the oncoming vehicle
- 100 meters—shoot a pen flare oblique to the vehicle
- 75 meters—use the M16 service rifle, fire warning shots at the road and oblique
- 50 meters—switch to the mounted turret gun, fire disabling shots into the vehicle's grill, hood, and engine block
- 25 meters—fire kill shots into the driver's windshield'''
    
    content = re.sub(eof_pattern, eof_replacement, content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Apostrophe fixes complete. Output written to {output_file}")

if __name__ == "__main__":
    target_file = DOCS_DIR / "Tomb of the Unknowns.md"
    fix_apostrophes(target_file, target_file)
