#!/usr/bin/env python3
"""
LingFrame Desktop Launcher - Native desktop wrapper for the Streamlit web app.

Uses PyWebView to create a native OS window that wraps the Streamlit application.
This allows LingFrame to run as a standalone desktop application.

Usage:
    python desktop/launcher.py

Or when packaged:
    ./LingFrame.app (macOS)
    LingFrame.exe (Windows)
"""

from __future__ import annotations

import atexit
import multiprocessing
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Determine the project root
if getattr(sys, 'frozen', False):
    # Running as compiled app (PyInstaller)
    PROJECT_ROOT = Path(sys._MEIPASS)
    APP_ROOT = Path(sys.executable).parent
else:
    # Running as script
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    APP_ROOT = PROJECT_ROOT

# Configuration
APP_NAME = "LingFrame"
APP_TITLE = "LingFrame - Writing Analysis"
DEFAULT_PORT = 8501
BACKUP_PORTS = [8502, 8503, 8504, 8505]
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 850
STARTUP_TIMEOUT = 30  # seconds


def find_available_port() -> int:
    """Find an available port for the Streamlit server."""
    ports_to_try = [DEFAULT_PORT] + BACKUP_PORTS

    for port in ports_to_try:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue

    # Fallback: let OS pick a port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


def is_server_ready(port: int) -> bool:
    """Check if the Streamlit server is responding."""
    try:
        import urllib.request
        url = f"http://localhost:{port}/_stcore/health"
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def wait_for_server(port: int, timeout: int = STARTUP_TIMEOUT) -> bool:
    """Wait for the Streamlit server to become ready."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_server_ready(port):
            return True
        time.sleep(0.5)

    return False


def run_streamlit_server(port: int):
    """Run the Streamlit server as a subprocess."""
    # Determine paths
    if getattr(sys, 'frozen', False):
        # Running as compiled app
        app_script = PROJECT_ROOT / "app" / "streamlit_app.py"
        python_exec = sys.executable
    else:
        # Running as script
        app_script = PROJECT_ROOT / "app" / "streamlit_app.py"
        python_exec = sys.executable

    # Streamlit command
    cmd = [
        python_exec,
        "-m", "streamlit",
        "run",
        str(app_script),
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "light",
    ]

    # Set environment
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"

    # Start server
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
    )

    return process


class StreamlitServer:
    """Manages the Streamlit server lifecycle."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.port: int = 0

    def start(self) -> bool:
        """Start the Streamlit server."""
        self.port = find_available_port()
        print(f"Starting Streamlit server on port {self.port}...")

        self.process = run_streamlit_server(self.port)

        # Wait for server to be ready
        if wait_for_server(self.port):
            print(f"Streamlit server is ready at http://localhost:{self.port}")
            return True
        else:
            print("Failed to start Streamlit server within timeout")
            self.stop()
            return False

    def stop(self):
        """Stop the Streamlit server."""
        if self.process:
            print("Stopping Streamlit server...")

            # Try graceful termination first
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if necessary
                self.process.kill()
                self.process.wait()

            self.process = None
            print("Streamlit server stopped")

    def get_url(self) -> str:
        """Get the server URL."""
        return f"http://localhost:{self.port}"


def create_window(server: StreamlitServer):
    """Create the native application window."""
    try:
        import webview
    except ImportError:
        print("Error: pywebview is not installed.")
        print("Install it with: pip install pywebview")
        sys.exit(1)

    # Create window
    window = webview.create_window(
        title=APP_TITLE,
        url=server.get_url(),
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=True,
        min_size=(800, 600),
    )

    # Start the GUI event loop
    # This blocks until the window is closed
    webview.start()


def cleanup(server: StreamlitServer):
    """Cleanup function called on exit."""
    server.stop()


def main():
    """Main entry point for the desktop application."""
    print(f"Starting {APP_NAME}...")
    print(f"Project root: {PROJECT_ROOT}")

    # Check for required dependencies
    try:
        import webview
    except ImportError:
        print("\nError: pywebview is not installed.")
        print("This is required for the desktop application.")
        print("\nInstall it with:")
        print("  pip install pywebview")
        print("\nOr run the web version instead:")
        print("  python run_web.py")
        sys.exit(1)

    # Create and start the server
    server = StreamlitServer()

    # Register cleanup handlers
    atexit.register(cleanup, server)
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    # Start the server
    if not server.start():
        print("Failed to start the application server.")
        sys.exit(1)

    try:
        # Create and run the native window
        create_window(server)
    finally:
        # Ensure cleanup happens
        cleanup(server)

    print(f"{APP_NAME} closed.")


if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()
