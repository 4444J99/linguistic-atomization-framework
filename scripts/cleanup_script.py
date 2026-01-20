#!/usr/bin/env python3
"""Comprehensive cleanup script for Tomb of the Unknowns manuscript"""

import re
from pathlib import Path

from project_paths import DOCS_DIR

def clean_manuscript(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix encoding artifacts: � → —
    content = content.replace('\ufffd', '—')
    
    # Fix apostrophes and quotes
    content = content.replace('\u2019', "'")
    
    # Capitalize "Marine" when referring to a person (but not mid-word like "submarine")
    # Careful pattern: whole word "marine" or "marines" but not in compounds
    content = re.sub(r'\bmarine\b(?!\')', 'Marine', content)
    content = re.sub(r'\bmarines\b(?!\')', 'Marines', content)
    
    # Add headers for sections (find section titles at start of paragraphs)
    section_titles = [
        "Available in Standard Sizes",
        "Instead of a Bayonet",
        "On the Rifle Range",
        "Enunciation Starts with E",
        "Calls of Duty",
        "Stateside 1",
        "Non-deployable Unit",
        "Stateside 2",
        "Iconography",
        "To Deaden the Nerve",
        "Military Town",
        "Fair in Love",
        "A Brief and Partial History of Attack and Defense",
        "The Smallest Scale",
        "Sandstorm 1",
        "The Cleaners",
        "Dearest Marines",
        "Demonstration in a Throughway",
        "Parallel Search Processing",
        "Natural as a Sigh",
        "Sandstorm 2",
        "Objects in Space",
        "First Contact",
        "Kind of Combat Action",
        "Stateside 3",
        "Sandstorm 3",
        "Touching",
        "Turnover",
        "Ram Skull",
        "Clearing and Being Cleared",
        "Cardinal",
        "Sandstorm 4",
        "Steel Beneath Your Chin",
        "Privates First Class",
        "All Hallows",
        "In Ram Corpse",
        "Sandstorm 5",
        "Like Closing Distance",
        "Kings of Thanksgiving",
        "Weapons We Talk About When We Talk About",
        "Held Fast in Place",
        "One Cries Abandon",
        "Down from Sinjar",
        "Sandstorm 6",
        "Rabia Railway",
        "Vulnerability in a Sense",
        "Laurel and Patina",
        "Finely Ground and Unfiltered",
        "Kilroy Was There",
        "Red Cross Letters Never Burn",
        "Sandstorm 7"
    ]
    
    for title in section_titles:
        # Match title at start of line followed by space and capital letter
        pattern = f'\n{re.escape(title)} ([A-Z])'
        replacement = f'\n## {title}\n\n\\1'
        content = re.sub(pattern, replacement, content)
    
    # Fix spacing issues
    content = re.sub(r' ,', ',', content)  # Remove space before comma
    content = re.sub(r'  +', ' ', content)  # Collapse multiple spaces
    
    # Light copyedit: fix obvious typos
    content = content.replace('know judgement', 'no judgement')
    content = content.replace('struggled get out', 'struggled to get out')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Cleanup complete. Output written to {output_file}")

if __name__ == "__main__":
    clean_manuscript(
        DOCS_DIR / "Tomb of the Unknowns.md",
        DOCS_DIR / "Tomb of the Unknowns_cleaned.md"
    )
