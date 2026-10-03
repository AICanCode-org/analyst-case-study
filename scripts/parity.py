#!/usr/bin/env python3
"""Cross-track parity: do two or more answers.json files say the same thing?

    python3 scripts/parity.py contract/golden/answers-2026-06.json tracks/*/out/answers.json

Every file is compared with the first. Integers, strings, booleans, nulls and list lengths must be
identical; floats may differ by at most 1e-9 relative (1e-12 absolute near zero). `generator`
(which track and version wrote the file) is ignored. Standard library only. Exit code 1 on any
difference, with the JSON path of each one.

    python3 scripts/parity.py --backcompat contract/golden/answers-2026-06.json out/answers.json

--backcompat (v1.1): the first file is an OLDER answers file. Fields that only the newer files have are
allowed (schema changes are additive), and schema_version / dataset.contract_version may differ.
Every field the old file has must still be there with the same value.
"""

from __future__ import annotations

import json
import math
import sys

REL, ABS = 1e-9, 1e-12
IGNORE = {"generator"}
BACKCOMPAT_IGNORE = {"$.schema_version", "$.dataset.contract_version"}


def diff(a, b, path="$", subset=False):
    if subset and path in BACKCOMPAT_IGNORE:
        return
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str) or isinstance(b, str):
        if a != b or type(a) is not type(b):
            yield f"{path}: {a!r} != {b!r}"
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            if a != b:
                yield f"{path}: {a} != {b}"
        elif not math.isclose(a, b, rel_tol=REL, abs_tol=ABS):
            yield f"{path}: {a!r} != {b!r}"
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if path == "$" and k in IGNORE:
                continue
            if subset and k not in a:
                continue
            if k not in a or k not in b:
                yield f"{path}.{k}: only in {'second' if k in b else 'first'} file"
            else:
                yield from diff(a[k], b[k], f"{path}.{k}", subset)
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield f"{path}: {len(a)} items != {len(b)} items"
            return
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            yield from diff(x, y, f"{path}[{i}]", subset)
        return
    yield f"{path}: {type(a).__name__} != {type(b).__name__}"


def main(paths: list[str]) -> int:
    subset = "--backcompat" in paths
    paths = [p for p in paths if p != "--backcompat"]
    if len(paths) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    docs = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            docs.append(json.load(fh))
    bad = 0
    for p, d in zip(paths[1:], docs[1:], strict=True):
        problems = list(diff(docs[0], d, subset=subset))
        track = d.get("generator", {}).get("track", "?")
        if problems:
            bad += 1
            print(f"DIFFERENT  {p} ({track}): {len(problems)} difference(s)")
            for line in problems[:25]:
                print("   ", line)
        else:
            print(f"IDENTICAL  {p} ({track})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
