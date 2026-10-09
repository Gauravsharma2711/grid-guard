"""CLI runner to launch both the FastAPI backend and React frontend concurrently."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    """Launch API and React Frontend simultaneously for seamless local operation."""
    root_dir = Path(__file__).resolve().parent.parent
    frontend_dir = root_dir / "frontend"
    api_script = root_dir / "scripts" / "run_api.py"

    print("=" * 65)
    print("GRID-GUARD INTEGRATED APPLICATION RUNNER")
    print("=" * 65)
    print("Starting FastAPI Backend (http://localhost:8000)...")

    env = os.environ.copy()
    api_proc = subprocess.Popen([sys.executable, str(api_script)], env=env)

    # Wait for API to initialize
    print("Waiting 3 seconds for FastAPI lifespan initialization...")
    time.sleep(3)

    print("Starting React Frontend (http://localhost:5173)...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        cwd=str(frontend_dir),
        shell=True,
    )

    print("\nServices active:")
    print("  - FastAPI API:       http://localhost:8000  (Docs: /docs)")
    print("  - React Frontend:    http://localhost:5173")
    print("Press Ctrl+C to terminate both services.\n")

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        for p in (frontend_proc, api_proc):
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("Grid-Guard services terminated.")


if __name__ == "__main__":
    main()

