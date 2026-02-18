"""Run context and artifact management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


class RunContext:
    """Manages a run output directory and artifact saving.

    Creates a timestamped directory under *output_dir* and provides
    convenience methods for persisting configs, results, and plots.

    Parameters
    ----------
    output_dir : str
        Base output directory (default ``"./runs"``).
    run_id : str
        Optional identifier appended to the directory name.
    """

    def __init__(self, output_dir: str = "./runs", run_id: str = "") -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        suffix = f"_{run_id}" if run_id else ""
        self.run_dir = Path(output_dir) / f"run_{timestamp}{suffix}"
        self.plots_dir = self.run_dir / "plots"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(exist_ok=True)

    def save_config_snapshot(self, config: dict[str, Any]) -> Path:
        """Save config snapshot as YAML.

        Parameters
        ----------
        config : dict
            Configuration dictionary to serialise.

        Returns
        -------
        Path
            Path to the saved YAML file.
        """
        path = self.run_dir / "config_snapshot.yaml"
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        return path

    def save_results_parquet(self, df: pd.DataFrame) -> Path:
        """Save results as parquet.

        Parameters
        ----------
        df : pandas.DataFrame
            Results DataFrame.

        Returns
        -------
        Path
            Path to the saved parquet file.
        """
        path = self.run_dir / "results.parquet"
        df.to_parquet(path, index=False)
        return path

    def save_breakdown_csv(self, df: pd.DataFrame) -> Path:
        """Save link breakdown as CSV.

        Parameters
        ----------
        df : pandas.DataFrame
            Breakdown DataFrame.

        Returns
        -------
        Path
            Path to the saved CSV file.
        """
        path = self.run_dir / "link_breakdown.csv"
        df.to_csv(path, index=False)
        return path

    @property
    def beam_maps_dir(self) -> Path:
        """Directory for beam map artifacts (created on first access)."""
        d = self.run_dir / "beam_maps"
        d.mkdir(exist_ok=True)
        return d

    def save_beammap_parquet(self, df: pd.DataFrame) -> Path:
        """Save beam map results as parquet.

        Parameters
        ----------
        df : pandas.DataFrame
            Beam map DataFrame from ``BeamMap.to_dataframe()``.

        Returns
        -------
        Path
            Path to the saved parquet file.
        """
        path = self.beam_maps_dir / "beam_map.parquet"
        df.to_parquet(path, index=False)
        return path
