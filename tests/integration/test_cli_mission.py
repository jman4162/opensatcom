"""Integration test: CLI mission command produces artifacts."""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

MISSION_CONFIG = {
    "project": {"name": "mission_test", "seed": 42},
    "scenario": {
        "name": "test_dl",
        "direction": "downlink",
        "freq_hz": 19.7e9,
        "bandwidth_hz": 200e6,
        "polarization": "RHCP",
        "required_metric": "ebn0_db",
        "required_value": 6.0,
    },
    "terminals": {
        "tx": {"name": "sat", "lat_deg": 0.0, "lon_deg": 0.0, "alt_m": 550000.0},
        "rx": {
            "name": "ut",
            "lat_deg": 47.6,
            "lon_deg": -122.3,
            "alt_m": 50.0,
            "system_noise_temp_k": 500.0,
        },
    },
    "antenna": {
        "tx": {"model": "parametric", "parametric": {"gain_dbi": 30.0}},
        "rx": {"model": "parametric", "parametric": {"gain_dbi": 35.0}},
    },
    "rf_chain": {"tx_power_w": 200.0, "tx_losses_db": 2.0, "rx_noise_temp_k": 500.0},
    "propagation": {"model": "composite", "components": [{"type": "fspl"}]},
    "world": {
        "enabled": True,
        "t0_s": 0,
        "t1_s": 60,
        "dt_s": 1.0,
        "ops_policy": {
            "min_elevation_deg": 10,
            "max_scan_deg": 60,
        },
    },
}


@pytest.mark.integration
class TestCLIMission:
    def test_mission_produces_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mission_config.yaml"
            config = {
                **MISSION_CONFIG,
                "project": {**MISSION_CONFIG["project"], "output_dir": tmpdir},
            }
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = subprocess.run(
                ["opensatcom", "mission", str(config_path)],
                capture_output=True, text=True, timeout=60,
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "Mission simulation complete" in result.stdout

            # Check artifacts were created
            run_dirs = [
                d for d in Path(tmpdir).iterdir()
                if d.is_dir() and d.name.startswith("run_")
            ]
            assert len(run_dirs) == 1

            run_dir = run_dirs[0]
            assert (run_dir / "config_snapshot.yaml").exists()
            assert (run_dir / "results.parquet").exists()
            assert (run_dir / "report.html").exists()
