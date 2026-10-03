"""Command line: python -m funnellens_sql run --data ../../data/raw/2026-06 --out out"""

from __future__ import annotations

import argparse
import sys

import duckdb

from .report import build_report
from .runner import ContractError, analyse, write_answers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="funnellens_sql", description="FunnelLens analysis (SQL track, DuckDB)")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="clean an export, check the contract and write answers.json")
    run.add_argument("--data", required=True, help="export folder, e.g. ../../data/raw/2026-06")
    run.add_argument("--out", default="out", help="output folder (default: out)")
    run.add_argument(
        "--contract", default=None, help="contract file (default: $CONTRACT_PATH or contract/data-contract.yaml)"
    )
    rep = sub.add_parser("report", help="run, then write out/report.md with every result view as a table")
    for p in (rep,):
        p.add_argument("--data", required=True)
        p.add_argument("--out", default="out")
        p.add_argument("--contract", default=None)
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            path = build_report(args.data, args.out, args.contract)
            print(f"wrote {path}")
            return 0
        answers = analyse(args.data, args.contract)
        path = write_answers(answers, args.out)
    except ContractError as exc:
        print(f"funnellens_sql: {exc}", file=sys.stderr)
        return 3
    except (OSError, duckdb.IOException) as exc:
        print(f"funnellens_sql: {exc}", file=sys.stderr)
        return 2
    print(
        f"wrote {path}: export {answers['dataset']['export']}, recommendation {answers['decision']['recommendation']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
