"""Tests for config loading and validation."""

import tempfile

import pytest
import yaml

from opensatcom.io.config_loader import load_config

VALID_CONFIG = {
    "project": {"name": "test_project", "seed": 42, "output_dir": "./runs"},
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
        "tx": {"name": "sat", "lat_deg": 0.0, "lon_deg": 0.0, "alt_m": 550e3},
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
    "rf_chain": {
        "tx_power_w": 200.0,
        "tx_losses_db": 2.0,
        "rx_noise_temp_k": 500.0,
    },
    "propagation": {
        "model": "composite",
        "components": [{"type": "fspl"}],
    },
}


class TestConfigLoader:
    def test_valid_config_loads(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            yaml.dump(VALID_CONFIG, f)
            f.flush()
            cfg = load_config(f.name)
        assert cfg.project.name == "test_project"
        assert cfg.scenario.freq_hz == 19.7e9
        assert cfg.terminals.rx.system_noise_temp_k == 500.0

    def test_missing_required_fields_rejected(self) -> None:
        bad_config = {"project": {"name": "test"}}
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            yaml.dump(bad_config, f)
            f.flush()
            with pytest.raises(Exception):  # Pydantic ValidationError
                load_config(f.name)

    def test_invalid_direction_rejected(self) -> None:
        bad_config = dict(VALID_CONFIG)
        bad_config = {**VALID_CONFIG}
        bad_config["scenario"] = {**VALID_CONFIG["scenario"], "direction": "sideways"}
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            yaml.dump(bad_config, f)
            f.flush()
            with pytest.raises(Exception):
                load_config(f.name)

    def test_pam_antenna_config(self) -> None:
        config = {**VALID_CONFIG}
        config["antenna"] = {
            "tx": {
                "model": "pam",
                "pam": {"nx": 16, "ny": 16, "dx_lambda": 0.5, "dy_lambda": 0.5},
            },
            "rx": {"model": "parametric", "parametric": {"gain_dbi": 35.0}},
        }
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            yaml.dump(config, f)
            f.flush()
            cfg = load_config(f.name)
        assert cfg.antenna.tx.model == "pam"
        assert cfg.antenna.tx.pam is not None
        assert cfg.antenna.tx.pam.nx == 16
