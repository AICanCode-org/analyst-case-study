"""python -m funnellens_dashboard prepare --answers PATH [--out static]"""

from __future__ import annotations

import argparse
import sys

from .prepare import AnswersError, prepare


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="funnellens_dashboard")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="validate answers.json and write static/ (answers, narrative, one-pager)")
    p.add_argument("--answers", required=True)
    p.add_argument("--out", default="static")
    args = parser.parse_args(argv)
    try:
        narrative = prepare(args.answers, args.out)
    except AnswersError as exc:
        print(f"funnellens_dashboard: {exc}", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"funnellens_dashboard: {exc}", file=sys.stderr)
        return 2
    note = f"fallback: {narrative['reason']}" if narrative["fallback"] else "ok"
    print(f"prepared {args.out}: narrative source {narrative['source']} ({note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
