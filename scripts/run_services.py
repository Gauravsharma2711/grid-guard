"""CLI runner to launch both the FastAPI backend and Streamlit dashboard concurrently."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    """Launch API and Dashboard simultaneously for seamless local demo."""
    root_dir = Path(__file__).resolve().parent.parent
    dashboard_script = root_dir / "scripts" / "run_dashboard.py"
    api_script = root_dir / "scripts" / "run_api.py"

    print("=" * 65)
    print("⚡ GRID-GUARD INTEGRATED APPLICATION RUNNER")
    print("=" * 65)
    print("Starting FastAPI Backend (http://localhost:8000)...")

    env = os.environ.copy()
    api_proc = subprocess.Popen([sys.executable, str(api_script)], env=env)

    # Wait for API to initialize
    print("Waiting 3 seconds for FastAPI lifespan initialization...")
    time.sleep(3)

    print("Starting Streamlit Dashboard (http://localhost:8501)...")
    dash_proc = subprocess.Popen([sys.executable, str(dashboard_script)], env=env)

    print("\nServices active:")
    print("  • FastAPI API:       http://localhost:8000  (Docs: /docs)")
    print("  • Streamlit UI:      http://localhost:8501")
    print("Press Ctrl+C to terminate both services.\n")

    try:
        dash_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        for p in (dash_proc, api_proc):
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("Grid-Guard services terminated.")


if __name__ == "__main__":
    main()
