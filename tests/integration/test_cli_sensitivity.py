"""Integration test: CLI sensitivity command."""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml


def _salib_available() -> bool:
    try:
        import SALib  # noqa: F401
        return True
    except ImportError:
        return False


SENSITIVITY_CONFIG = {
    "project": {"name": "sens_test", "seed": 42},
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
    "trades": {
        "parameters": {
            "tx_power_w": [50.0, 500.0],
            "freq_hz": [10e9, 30e9],
        },
    },
}


@pytest.mark.integration
@pytest.mark.skipif(not _salib_available(), reason="SALib not installed")
class TestCLISensitivity:
    def test_sensitivity_produces_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            config = {
                **SENSITIVITY_CONFIG,
                "project": {**SENSITIVITY_CONFIG["project"], "output_dir": tmpdir},
            }
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = subprocess.run(
                ["opensatcom", "sensitivity", str(config_path),
                 "--metric", "margin_db", "-n", "32"],
                capture_output=True, text=True, timeout=120,
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "Sobol indices" in result.stdout
            assert "sensitivity.html" in result.stdout

            # Check plot was created
            assert (Path(tmpdir) / "sensitivity.html").exists()
