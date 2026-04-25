import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

import uvicorn

from atlas_backend.api import create_app
from atlas_backend.config import default_config
from atlas_backend.logging_config import configure_logging
from atlas_backend.module_infer import infer_modules
from atlas_backend.scanner import scan_repo

LOGGER = logging.getLogger(__name__)


def main() -> None:
    config = default_config()
    configure_logging(config.log_path)
    parser = argparse.ArgumentParser(prog="atlas")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan")
    scan_parser.add_argument("--repo", required=True)
    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    try:
        if args.command == "scan":
            scan = scan_repo(Path(args.repo))
            payload = {"repo": scan.repo_name, "modules": [asdict(module) for module in infer_modules(scan)]}
            print(json.dumps(payload, default=str, indent=2))
        elif args.command == "serve":
            LOGGER.info("Starting Project Atlas API on %s:%s", args.host, args.port)
            uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")
    except Exception as exc:
        LOGGER.exception("Project Atlas command failed")
        print(f"Project Atlas stopped: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()