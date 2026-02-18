"""Integration tests for trades CLI commands."""

from pathlib import Path

import pytest
import yaml

from opensatcom.cli.main import cmd_doe, cmd_pareto


@pytest.mark.integration
class TestCLITrades:
    def test_doe_command(self, tmp_path: Path) -> None:
        """opensatcom doe generates cases.parquet."""
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

        import argparse

        args = argparse.Namespace(config=str(config_path), n=20, method="lhs")
        cmd_doe(args)

        cases_path = tmp_path / "cases.parquet"
        assert cases_path.exists()

        import pandas as pd

        df = pd.read_parquet(cases_path)
        assert len(df) == 20
        assert "freq_hz" in df.columns

    def test_pareto_command(self, tmp_path: Path) -> None:
        """opensatcom pareto extracts Pareto front."""
        import pandas as pd

        results = pd.DataFrame({
            "cost": [1.0, 2.0, 3.0, 1.5],
            "throughput": [1.0, 3.0, 2.0, 2.5],
        })
        results_path = tmp_path / "results.parquet"
        results.to_parquet(results_path, index=False)

        import argparse

        args = argparse.Namespace(results=str(results_path), x="cost", y="throughput")
        cmd_pareto(args)

        pareto_path = tmp_path / "pareto.parquet"
        assert pareto_path.exists()

        plot_path = tmp_path / "pareto.png"
        assert plot_path.exists()
