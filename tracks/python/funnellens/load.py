"""M1: load the raw CSVs exactly as text. Types are decided in clean.py, never guessed by the reader."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

TABLES = ("users", "sessions", "events", "orders")


def load_raw(data_dir: str | Path, contract: dict) -> dict[str, pd.DataFrame]:
    """Read every table as strings (empty cells stay ""), and fail fast if a contract column is missing."""
    # TODO(M1) load_raw: read every CSV as TEXT (no type guessing, empty strings stay empty strings); a missing
    # file or column is a ContractError. Spec: contract/questions.md §1-2; tests: load.
    raise NotImplementedError("TODO(M1) load_raw: see the comment above")
