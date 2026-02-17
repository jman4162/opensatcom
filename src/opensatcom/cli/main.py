"""OpenSatCom CLI entry point."""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opensatcom",
        description="Professional-grade satellite communications engineering toolkit",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    sub = parser.add_subparsers(dest="command")

    # opensatcom run
    run_parser = sub.add_parser("run", help="Snapshot link evaluation")
    run_parser.add_argument("config", help="Path to YAML config file")

    # opensatcom mission
    mission_parser = sub.add_parser("mission", help="Time-series mission simulation")
    mission_parser.add_argument("config", help="Path to YAML config file")

    # opensatcom doe
    doe_parser = sub.add_parser("doe", help="Design of experiments")
    doe_parser.add_argument("config", help="Path to YAML config file")
    doe_parser.add_argument("-n", type=int, default=200, help="Number of cases")
    doe_parser.add_argument("--method", default="lhs", help="Sampling method")

    # opensatcom batch
    batch_parser = sub.add_parser("batch", help="Batch evaluation from parquet")
    batch_parser.add_argument("cases", help="Path to cases parquet file")
    batch_parser.add_argument("--parallel", action="store_true", help="Enable parallel execution")

    # opensatcom report
    report_parser = sub.add_parser("report", help="Generate report from results")
    report_parser.add_argument("results", help="Path to results parquet file")
    report_parser.add_argument("--format", default="html", choices=["html", "pdf"])

    # opensatcom pareto
    pareto_parser = sub.add_parser("pareto", help="Pareto extraction from results")
    pareto_parser.add_argument("results", help="Path to results parquet file")
    pareto_parser.add_argument("--x", required=True, help="X-axis metric")
    pareto_parser.add_argument("--y", required=True, help="Y-axis metric")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Command dispatch will be implemented per-module
    print(f"opensatcom {args.command}: not yet implemented")
    sys.exit(1)
