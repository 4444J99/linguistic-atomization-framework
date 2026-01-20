#!/usr/bin/env python3
"""
LingFrame Web Application Launcher

Launches the Streamlit web interface for non-technical users.

Usage:
    python run_web.py
    # or
    ./new_venv/bin/python run_web.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit web application."""
    # Get the directory containing this script
    script_dir = Path(__file__).resolve().parent

    # Find the streamlit executable
    venv_streamlit = script_dir / "new_venv" / "bin" / "streamlit"

    if venv_streamlit.exists():
        streamlit_cmd = str(venv_streamlit)
    else:
        # Fall back to system streamlit
        streamlit_cmd = "streamlit"

    # App path
    app_path = script_dir / "app" / "streamlit_app.py"

    print("=" * 50)
    print("  LingFrame - Writing Analysis for Everyone")
    print("=" * 50)
    print()
    print("Starting web interface...")
    print("Open your browser to: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop the server")
    print()

    # Run streamlit
    subprocess.run([
        streamlit_cmd, "run", str(app_path),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ])


if __name__ == "__main__":
    main()
