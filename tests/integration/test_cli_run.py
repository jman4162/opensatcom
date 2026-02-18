"""Integration test: CLI run command produces artifacts."""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

MINIMAL_CONFIG = {
    "project": {"name": "cli_test", "seed": 42},
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
}


@pytest.mark.integration
class TestCLIRun:
    def test_run_produces_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            config = {
                **MINIMAL_CONFIG,
                "project": {**MINIMAL_CONFIG["project"], "output_dir": tmpdir},
            }
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = subprocess.run(
                ["opensatcom", "run", str(config_path)],
                capture_output=True, text=True, timeout=30,
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "Margin:" in result.stdout

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
            assert (run_dir / "link_breakdown.csv").exists()

    def test_run_with_example_config(self) -> None:
        """Run with the repo's example config."""
        example_path = Path(__file__).parent.parent.parent / "examples" / "example_config.yaml"
        if not example_path.exists():
            pytest.skip("Example config not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Override output_dir
            with open(example_path) as f:
                config = yaml.safe_load(f)
            config["project"]["output_dir"] = tmpdir

            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = subprocess.run(
                ["opensatcom", "run", str(config_path)],
                capture_output=True, text=True, timeout=30,
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
