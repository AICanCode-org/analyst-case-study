"""Command line: python -m funnellens run --data ../../data/raw/2026-06 --out out"""

from __future__ import annotations

import argparse
import sys

from .contract import ContractError
from .pipeline import analyse, write_answers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="funnellens", description="FunnelLens analysis (Python track)")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="clean an export, check the contract and write answers.json")
    run.add_argument("--data", required=True, help="export folder, e.g. ../../data/raw/2026-06")
    run.add_argument("--out", default="out", help="output folder (default: out)")
    run.add_argument(
        "--contract", default=None, help="contract file (default: $CONTRACT_PATH or contract/data-contract.yaml)"
    )
    args = parser.parse_args(argv)
    try:
        answers = analyse(args.data, args.contract)
        path = write_answers(answers, args.out)
    except ContractError as exc:
        print(f"funnellens: {exc}", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"funnellens: {exc}", file=sys.stderr)
        return 2
    d = answers["decision"]
    print(f"wrote {path}: export {answers['dataset']['export']}, recommendation {d['recommendation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
