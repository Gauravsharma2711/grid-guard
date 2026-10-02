"""CLI runner for the Grid-Guard Streamlit Operational Dashboard."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run Streamlit dashboard application."""
    root_dir = Path(__file__).resolve().parent.parent
    app_path = root_dir / "src" / "grid_guard" / "dashboard" / "app.py"

    parser = argparse.ArgumentParser(description="Run the Grid-Guard Streamlit Dashboard")
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port for Streamlit dashboard (default: 8501)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind (default: 0.0.0.0)",
    )
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.port),
        "--server.address",
        args.host,
        "--browser.serverAddress",
        "localhost",
        "--theme.base",
        "light",
    ]

    print(f"Launching Grid-Guard Dashboard on http://localhost:{args.port} ...")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
