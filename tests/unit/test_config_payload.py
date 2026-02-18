"""Tests for payload config section validation."""

import pytest

from opensatcom.io.config_loader import ProjectConfig, load_config


def _base_config() -> dict:
    """Minimal valid config with payload section."""
    return {
        "project": {"name": "test", "output_dir": "/tmp/test"},
        "scenario": {
            "name": "dl", "direction": "downlink", "freq_hz": 19.7e9,
            "bandwidth_hz": 200e6, "polarization": "RHCP",
            "required_metric": "ebn0_db", "required_value": 6.0,
        },
        "terminals": {
            "tx": {"name": "sat", "lat_deg": 0, "lon_deg": 0, "alt_m": 550e3},
            "rx": {"name": "ut", "lat_deg": 47, "lon_deg": -122, "alt_m": 50,
                   "system_noise_temp_k": 500},
        },
        "antenna": {
            "tx": {"model": "parametric", "parametric": {"gain_dbi": 35}},
            "rx": {"model": "parametric", "parametric": {"gain_dbi": 35}},
        },
        "rf_chain": {"tx_power_w": 100, "tx_losses_db": 0, "rx_noise_temp_k": 500},
        "propagation": {"model": "composite", "components": [{"type": "fspl"}]},
    }


class TestPayloadConfig:
    def test_valid_payload(self) -> None:
        cfg = _base_config()
        cfg["payload"] = {
            "beams": [
                {"beam_id": "B0", "az_deg": 0, "el_deg": 0, "tx_power_w": 100,
                 "cosine": {"peak_gain_dbi": 35, "theta_3db_deg": 2}},
                {"beam_id": "B1", "az_deg": 5, "el_deg": 0, "tx_power_w": 100,
                 "cosine": {"peak_gain_dbi": 35, "theta_3db_deg": 2}},
            ],
            "beam_selection": "max_gain",
            "grid_az_range": [-10, 10],
            "grid_el_range": [-10, 10],
            "grid_step_deg": 5.0,
        }
        pc = ProjectConfig.model_validate(cfg)
        assert pc.payload is not None
        assert len(pc.payload.beams) == 2
        assert pc.payload.beam_selection == "max_gain"

    def test_missing_beams_rejected(self) -> None:
        cfg = _base_config()
        cfg["payload"] = {
            "beams": [],
            "grid_az_range": [-10, 10],
            "grid_el_range": [-10, 10],
        }
        with pytest.raises(Exception, match="at least one beam"):
            ProjectConfig.model_validate(cfg)

    def test_invalid_beam_selection(self) -> None:
        cfg = _base_config()
        cfg["payload"] = {
            "beams": [{"beam_id": "B0", "az_deg": 0, "el_deg": 0, "tx_power_w": 100}],
            "beam_selection": "invalid",
            "grid_az_range": [-10, 10],
            "grid_el_range": [-10, 10],
        }
        with pytest.raises(Exception, match="beam_selection"):
            ProjectConfig.model_validate(cfg)

    def test_no_payload_section_allowed(self) -> None:
        """Config without payload is still valid (backward compatible)."""
        cfg = _base_config()
        pc = ProjectConfig.model_validate(cfg)
        assert pc.payload is None

    def test_beam_cosine_config(self) -> None:
        cfg = _base_config()
        cfg["payload"] = {
            "beams": [
                {"beam_id": "B0", "az_deg": 0, "el_deg": 0, "tx_power_w": 100,
                 "cosine": {"peak_gain_dbi": 35, "theta_3db_deg": 2,
                            "sidelobe_floor_dbi": -25}},
            ],
            "grid_az_range": [-5, 5],
            "grid_el_range": [-5, 5],
        }
        pc = ProjectConfig.model_validate(cfg)
        assert pc.payload is not None
        assert pc.payload.beams[0].cosine is not None
        assert pc.payload.beams[0].cosine.sidelobe_floor_dbi == -25.0

    def test_load_multibeam_example(self) -> None:
        """Load the multibeam example config file."""
        cfg = load_config("examples/multibeam_config.yaml")
        assert cfg.payload is not None
        assert len(cfg.payload.beams) == 4
        assert cfg.payload.beam_selection == "max_gain"

    def test_empty_beam_id_rejected(self) -> None:
        cfg = _base_config()
        cfg["payload"] = {
            "beams": [
                {"beam_id": "  ", "az_deg": 0, "el_deg": 0, "tx_power_w": 100},
            ],
            "grid_az_range": [-5, 5],
            "grid_el_range": [-5, 5],
        }
        with pytest.raises(Exception, match="beam_id"):
            ProjectConfig.model_validate(cfg)
