"""M1: load the raw CSVs exactly as text. Types are decided in clean.py, never guessed by the reader."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .contract import ContractError

TABLES = ("users", "sessions", "events", "orders")


def load_raw(data_dir: str | Path, contract: dict) -> dict[str, pd.DataFrame]:
    """Read every table as strings (empty cells stay ""), and fail fast if a contract column is missing."""
    raw = {}
    for table in TABLES:
        path = Path(data_dir) / f"{table}.csv"
        if not path.exists():
            raise ContractError(f"missing file {path}")
        df = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
        missing = [c for c in contract["raw"][table] if c not in df.columns]
        if missing:
            raise ContractError(f"{table}.csv is missing column(s) {missing}")
        raw[table] = df
    return raw
