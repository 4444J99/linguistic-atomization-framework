#!/usr/bin/env python3
"""
Linguistic Analysis Framework - Main Entry Point

Run the framework CLI:
    python lingframe.py run --project literary-analysis/MET4MORFOSES
    python lingframe.py atomize --project literary-analysis/MET4MORFOSES
    python lingframe.py analyze --project literary-analysis/MET4MORFOSES
    python lingframe.py visualize --project literary-analysis/MET4MORFOSES
    python lingframe.py list-modules
    python lingframe.py list-projects
"""

import sys
from cli.main import main

if __name__ == "__main__":
    sys.exit(main())
