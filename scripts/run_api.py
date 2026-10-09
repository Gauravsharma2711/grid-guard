"""CLI runner for the Grid-Guard FastAPI inference service."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(root_dir / "src") not in sys.path:
    sys.path.insert(0, str(root_dir / "src"))

import uvicorn  # noqa: E402

from grid_guard.config.settings import get_settings  # noqa: E402


def main() -> None:
    """Run uvicorn server with configuration defaults."""
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Run the Grid-Guard FastAPI Inference Server")
    parser.add_argument(
        "--host",
        type=str,
        default=settings.api.host,
        help=f"Bind host address (default: {settings.api.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", str(settings.api.port))),
        help=f"Bind port (default: {settings.api.port})",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.api.reload,
        help="Enable auto-reload on code change",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=settings.api.workers,
        help="Number of worker processes",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=settings.log_level.lower(),
        help=f"Logging level (default: {settings.log_level.lower()})",
    )

    args = parser.parse_args()

    print(
        f"Starting Grid-Guard NTL API on http://{args.host}:{args.port} "
        f"(Docs: http://{args.host}:{args.port}/docs)"
    )

    uvicorn.run(
        "grid_guard.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
