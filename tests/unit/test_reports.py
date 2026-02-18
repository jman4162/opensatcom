"""Tests for report generation."""

import tempfile
from pathlib import Path

from opensatcom.reports.snapshot import render_snapshot_report


class TestSnapshotReport:
    def test_generates_html(self) -> None:
        breakdown = {
            "tx_power_dbw": 23.01,
            "tx_losses_db": 2.0,
            "tx_antenna_gain_dbi": 29.05,
            "eirp_dbw": 50.06,
            "fspl_db": 179.92,
            "rain_db": 0.0,
            "gas_db": 0.0,
            "pointing_db": 0.0,
            "rx_antenna_gain_dbi": 35.0,
            "rx_system_temp_k": 500.0,
            "cn0_dbhz": 106.75,
            "ebn0_db": 23.74,
            "margin_db": 17.74,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.html"
            result = render_snapshot_report(breakdown, {}, out_path)
            assert result.exists()
            html = result.read_text()
            assert "17.74" in html
            assert "Snapshot Link Budget" in html
            assert "tx_power_dbw" in html

    def test_negative_margin_styling(self) -> None:
        breakdown = {"margin_db": -2.5, "eirp_dbw": 30.0}
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.html"
            result = render_snapshot_report(breakdown, {}, out_path)
            html = result.read_text()
            assert "#c62828" in html  # Red color for negative margin
