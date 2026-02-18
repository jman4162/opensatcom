"""Tests for batch runner."""

import pandas as pd

from opensatcom.trades.batch import BatchRunner


class TestBatchRunner:
    def test_evaluates_cases(self) -> None:
        cases = pd.DataFrame({
            "freq_hz": [12e9, 20e9, 30e9],
            "tx_power_w": [100.0, 100.0, 100.0],
        })
        runner = BatchRunner()
        results = runner.run(cases)
        assert len(results) == 3
        assert "margin_db" in results.columns
        assert "eirp_dbw" in results.columns
        assert "cn0_dbhz" in results.columns

    def test_margin_varies_with_frequency(self) -> None:
        cases = pd.DataFrame({
            "freq_hz": [4e9, 12e9, 30e9],
            "tx_power_w": [100.0, 100.0, 100.0],
        })
        runner = BatchRunner()
        results = runner.run(cases)
        margins = results["margin_db"].tolist()
        # Higher frequency = more path loss = lower margin
        assert margins[0] > margins[1] > margins[2]

    def test_preserves_input_columns(self) -> None:
        cases = pd.DataFrame({
            "freq_hz": [12e9],
            "tx_power_w": [100.0],
        })
        runner = BatchRunner()
        results = runner.run(cases)
        assert "freq_hz" in results.columns
        assert "tx_power_w" in results.columns
