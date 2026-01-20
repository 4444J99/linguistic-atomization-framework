from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
RAW_DATA_PATH = DATA_DIR / "raw" / "Tomb_of_the_Unknowns_atomized.json"
PROCESSED_DIR = DATA_DIR / "processed"
DERIVED_DIR = DATA_DIR / "derived"
VISUALIZATIONS_DIR = BASE_DIR / "visualizations"
SOURCE_MARKDOWN = DOCS_DIR / "Tomb of the Unknowns copy.md"

# Ensure output directories exist when scripts write files
for path in (PROCESSED_DIR, DERIVED_DIR, VISUALIZATIONS_DIR):
    path.mkdir(parents=True, exist_ok=True)
