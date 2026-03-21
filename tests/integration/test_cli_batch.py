"""Integration test: CLI batch command produces artifacts."""

import argparse
from pathlib import Path

import pandas as pd
import pytest
import yaml

from opensatcom.cli.main import cmd_batch, cmd_doe


@pytest.mark.integration
class TestCLIBatch:
    def test_batch_produces_results(self, tmp_path: Path) -> None:
        """DOE -> batch pipeline produces results.parquet."""
        # First generate cases via DOE
        config = {
            "trades": {
                "parameters": {
                    "freq_hz": [10e9, 30e9],
                    "tx_power_w": [10.0, 200.0],
                }
            }
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))

        doe_args = argparse.Namespace(config=str(config_path), n=5, method="lhs")
        cmd_doe(doe_args)

        cases_path = tmp_path / "cases.parquet"
        assert cases_path.exists()

        # Run batch on the generated cases
        batch_args = argparse.Namespace(cases=str(cases_path), parallel=False)
        cmd_batch(batch_args)

        results_path = tmp_path / "results.parquet"
        assert results_path.exists()

        df = pd.read_parquet(results_path)
        assert len(df) == 5
        assert "margin_db" in df.columns
        assert "cn0_dbhz" in df.columns
