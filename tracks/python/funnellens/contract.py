"""Read the shared data contract (contract/data-contract.yaml) and an export's manifest (export.json)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = REPO / "contract" / "data-contract.yaml"


class ContractError(Exception):
    """The input does not match the contract (missing column, failing error-level check...)."""


@dataclass(frozen=True)
class Export:
    name: str
    period_start: date
    period_end: date
    sample_rate: float

    @property
    def months(self) -> int:
        """Number of calendar months the period touches (Jan..Jun = 6)."""
        return (
            (self.period_end.year - self.period_start.year) * 12 + self.period_end.month - self.period_start.month + 1
        )


def contract_path(explicit: str | os.PathLike | None = None) -> Path:
    return Path(explicit or os.environ.get("CONTRACT_PATH") or DEFAULT_CONTRACT)


def load_contract(path: str | os.PathLike | None = None) -> dict:
    with open(contract_path(path), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_export(data_dir: str | os.PathLike) -> Export:
    meta_path = Path(data_dir) / "export.json"
    if not meta_path.exists():
        raise ContractError(f"{meta_path} not found: is --data an export folder like data/raw/2026-06?")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return Export(
        name=meta["export"],
        period_start=date.fromisoformat(meta["period_start"]),
        period_end=date.fromisoformat(meta["period_end"]),
        sample_rate=float(meta["sample_rate"]),
    )
