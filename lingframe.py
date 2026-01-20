#!/usr/bin/env python3
"""
Linguistic Analysis Framework - Main Entry Point

Run the framework CLI:
    python lingframe.py run --project tomb-of-the-unknowns
    python lingframe.py atomize --project tomb-of-the-unknowns
    python lingframe.py analyze --project tomb-of-the-unknowns
    python lingframe.py visualize --project tomb-of-the-unknowns
    python lingframe.py list-modules
    python lingframe.py list-projects
"""

import sys
from cli.main import main

if __name__ == "__main__":
    sys.exit(main())
