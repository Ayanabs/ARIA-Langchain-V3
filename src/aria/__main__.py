"""Command line: `python -m aria serve` (default), `preflight`, `catalog` (tool diagnostics) or
`ask "<question>"` (one question through the full flow, with a trace)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from aria.logging_setup import configure_logging
from aria.settings import ConfigError, Settings, get_settings

EXIT_PREFLIGHT_FAILED = 1
EXIT_CATALOG_FAILED = 1
EXIT_ASK_FAILED = 1
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


def catalog() -> None:
    """Load the tool catalog from the live backend contract and print why each tool is or isn't ready."""
    from aria.catalog.service import CatalogService

    settings = _load_settings_or_exit()
    configure_logging(settings.env.log_level, settings.secret_values())
    result = asyncio.run(CatalogService(settings).reload())
    print(json.dumps(result.diagnostics(), indent=2))
    if result.status != "ready":
        sys.exit(EXIT_CATALOG_FAILED)


def ask(question: str) -> None:
    """Answer one question through the full flow and print its full trace.

    The trace is also saved to the prompt history, where the Admin Console shows it. For local
    testing, backend calls run as the caller whose token is SPRING_BOOT_CONTRACT_TOKEN.
    """
    from aria.calling.backend import BackendInvoker
    from aria.catalog.service import CatalogService
    from aria.models.client import ChatModel, ModelError
    from aria.observability.store import PromptStore
    from aria.observability.trace import RequestTrace
    from aria.pipeline import answer_question

    settings = _load_settings_or_exit()
    configure_logging("WARNING", settings.secret_values())
    deployment = settings.deployment
    caller = deployment.chats.unauthenticated_user_id
    trace = RequestTrace(question, user_key=caller, username=caller, subject="command line")

    async def run() -> None:
        with trace.stage("catalog_load"):
            catalog = await CatalogService(settings).reload()
        trace.event("catalog_loaded", "Tool catalog loaded", stage="catalog_load", status=catalog.status)
        if catalog.status != "ready":
            trace.add_issue("catalog_unavailable", "request", catalog.error or "")
            trace.finish("error", failure="catalog_unavailable")
            return
        http = deployment.http
        await answer_question(
            question,
            catalog=catalog,
            tool_model=ChatModel(settings.tool_model, http),
            synthesis_model=ChatModel(settings.synthesis_model, http),
            invoke=BackendInvoker(settings, authorization=settings.contract_headers().get("Authorization")),
            prompts=deployment.prompts,
            max_fan_out=deployment.catalog.max_fan_out,
            trace=trace,
        )

    try:
        asyncio.run(run())
    except ModelError:
        pass  # Recorded in the trace, which is printed below.
    finally:
        history = deployment.observability
        if history.capture_prompts:
            PromptStore(history.prompt_history_file, history.max_prompts, history.retention_days).append(
                trace.to_prompt_record()
            )
    print(json.dumps(trace.to_prompt_record(), indent=2, ensure_ascii=False, default=str))
    if trace.status == "error":
        sys.exit(EXIT_ASK_FAILED)


COMMANDS = {"serve": serve, "preflight": preflight, "catalog": catalog}


def main() -> None:
    parser = argparse.ArgumentParser(prog="aria")
    parser.add_argument("command", nargs="?", default="serve", choices=[*COMMANDS, "ask"])
    parser.add_argument("question", nargs="?", help="the question, for the ask command")
    args = parser.parse_args()
    if args.command == "ask":
        if not args.question:
            parser.error("ask needs a question")
        ask(args.question)
    else:
        COMMANDS[args.command]()


if __name__ == "__main__":
    main()
