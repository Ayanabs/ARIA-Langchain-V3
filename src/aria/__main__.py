"""Command line: `python -m aria serve` (default) or `python -m aria preflight`."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from aria.logging_setup import configure_logging
from aria.settings import ConfigError, Settings, get_settings

EXIT_PREFLIGHT_FAILED = 1
EXIT_CONFIG_ERROR = 2


def _load_settings_or_exit() -> Settings:
    try:
        return get_settings()
    except ConfigError as error:
        print("Configuration error:", file=sys.stderr)
        for problem in error.problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(EXIT_CONFIG_ERROR)


def serve() -> None:
    import uvicorn

    from aria.app import create_app

    settings = _load_settings_or_exit()
    configure_logging(settings.env.log_level, settings.secret_values())
    uvicorn.run(create_app(settings), host=settings.env.host, port=settings.env.port, log_config=None)


def preflight() -> None:
    from aria.preflight import CheckStatus, run_preflight

    settings = _load_settings_or_exit()
    configure_logging(settings.env.log_level, settings.secret_values())
    report = asyncio.run(run_preflight(settings))
    print(json.dumps(report.to_dict(), indent=2))
    if report.status == CheckStatus.FAIL:
        sys.exit(EXIT_PREFLIGHT_FAILED)


def main() -> None:
    parser = argparse.ArgumentParser(prog="aria")
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "preflight"])
    args = parser.parse_args()
    if args.command == "serve":
        serve()
    else:
        preflight()


if __name__ == "__main__":
    main()
