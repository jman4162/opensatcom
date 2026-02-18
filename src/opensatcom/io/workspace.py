"""Run context and artifact management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


class RunContext:
    """Manages a run output directory and artifact saving."""

    def __init__(self, output_dir: str = "./runs", run_id: str = "") -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        suffix = f"_{run_id}" if run_id else ""
        self.run_dir = Path(output_dir) / f"run_{timestamp}{suffix}"
        self.plots_dir = self.run_dir / "plots"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(exist_ok=True)

    def save_config_snapshot(self, config: dict[str, Any]) -> Path:
        """Save config snapshot as YAML."""
        path = self.run_dir / "config_snapshot.yaml"
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        return path

    def save_results_parquet(self, df: pd.DataFrame) -> Path:
        """Save results as parquet."""
        path = self.run_dir / "results.parquet"
        df.to_parquet(path, index=False)
        return path

    def save_breakdown_csv(self, df: pd.DataFrame) -> Path:
        """Save link breakdown as CSV."""
        path = self.run_dir / "link_breakdown.csv"
        df.to_csv(path, index=False)
        return path
