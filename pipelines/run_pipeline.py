"""Unified CLI entry point for the Revenue Guardian pipelines.

Usage:
    python -m pipelines.run_pipeline monitor
    python -m pipelines.run_pipeline monitor --query "check today's revenue"
    python -m pipelines.run_pipeline ingest data/sample_sales.csv
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("revenue_guardian.run_pipeline")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Revenue Guardian pipeline runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    monitor_parser = subparsers.add_parser("monitor", help="Run the revenue monitoring pipeline")
    monitor_parser.add_argument(
        "--query", default="daily revenue monitor", help="Natural-language query/context for the run"
    )

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a CSV of sales rows into MySQL")
    ingest_parser.add_argument("csv_path", help="Path to a CSV file matching data/sample_sales.csv's columns")

    return parser


async def run_monitor_command(query: str) -> int:
    from pipelines.monitor_pipeline import run_monitor

    result = await run_monitor(query=query)
    print(json.dumps(result, indent=2, default=str))
    return 1 if result.get("error") else 0


def run_ingest_command(csv_path: str) -> int:
    from pipelines.ingest_pipeline import ingest_csv

    ingest_csv(csv_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "monitor":
        return asyncio.run(run_monitor_command(args.query))
    if args.command == "ingest":
        return run_ingest_command(args.csv_path)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
