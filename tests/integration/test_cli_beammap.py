"""Integration test: CLI beammap command produces artifacts."""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

BEAMMAP_CONFIG = {
    "project": {"name": "beammap_test", "seed": 42},
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
        "tx": {"model": "parametric", "parametric": {"gain_dbi": 35.0}},
        "rx": {"model": "parametric", "parametric": {"gain_dbi": 35.0}},
    },
    "rf_chain": {"tx_power_w": 100.0, "tx_losses_db": 0.0, "rx_noise_temp_k": 500.0},
    "propagation": {"model": "composite", "components": [{"type": "fspl"}]},
    "payload": {
        "beam_selection": "max_gain",
        "grid_az_range": [-5.0, 5.0],
        "grid_el_range": [-5.0, 5.0],
        "grid_step_deg": 5.0,
        "beams": [
            {
                "beam_id": "B0",
                "az_deg": -2.0,
                "el_deg": 0.0,
                "tx_power_w": 100.0,
                "cosine": {
                    "peak_gain_dbi": 35.0,
                    "theta_3db_deg": 2.0,
                },
            },
            {
                "beam_id": "B1",
                "az_deg": 2.0,
                "el_deg": 0.0,
                "tx_power_w": 100.0,
                "cosine": {
                    "peak_gain_dbi": 35.0,
                    "theta_3db_deg": 2.0,
                },
            },
        ],
    },
}


@pytest.mark.integration
class TestCLIBeammap:
    def test_beammap_produces_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "beammap_config.yaml"
            config = {
                **BEAMMAP_CONFIG,
                "project": {**BEAMMAP_CONFIG["project"], "output_dir": tmpdir},
            }
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = subprocess.run(
                ["opensatcom", "beammap", str(config_path)],
                capture_output=True, text=True, timeout=60,
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "Beam map evaluation complete" in result.stdout

            # Check artifacts were created
            run_dirs = [
                d for d in Path(tmpdir).iterdir()
                if d.is_dir() and d.name.startswith("run_")
            ]
            assert len(run_dirs) == 1

            run_dir = run_dirs[0]
            assert (run_dir / "config_snapshot.yaml").exists()
            assert (run_dir / "beam_maps" / "beam_map.parquet").exists()
            assert (run_dir / "report.html").exists()

    def test_beammap_with_example_config(self) -> None:
        """Run with the repo's multibeam example config."""
        example_path = (
            Path(__file__).parent.parent.parent / "examples" / "multibeam_config.yaml"
        )
        if not example_path.exists():
            pytest.skip("Multibeam example config not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(example_path) as f:
                config = yaml.safe_load(f)
            config["project"]["output_dir"] = tmpdir

            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = subprocess.run(
                ["opensatcom", "beammap", str(config_path)],
                capture_output=True, text=True, timeout=60,
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
