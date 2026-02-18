"""Tests for cascaded RF chain config loading and building."""

from opensatcom.io.config_loader import ProjectConfig, RFStageConfig


class TestRFStageConfig:
    def test_stage_config_construction(self) -> None:
        s = RFStageConfig(name="LNA", gain_db=20.0, nf_db=1.0)
        assert s.name == "LNA"
        assert s.iip3_dbm is None

    def test_stage_with_iip3(self) -> None:
        s = RFStageConfig(name="LNA", gain_db=20.0, nf_db=1.0, iip3_dbm=-10.0)
        assert s.iip3_dbm == -10.0


class TestRFChainConfigWithStages:
    """Test that config with stages builds a cascaded chain."""

    MINIMAL_CONFIG = {
        "project": {"name": "test"},
        "scenario": {
            "name": "test",
            "direction": "downlink",
            "freq_hz": 19.7e9,
            "bandwidth_hz": 500e6,
            "polarization": "RHCP",
            "required_metric": "cn0_dbhz",
            "required_value": 80.0,
        },
        "terminals": {
            "tx": {
                "name": "sat",
                "lat_deg": 0.0,
                "lon_deg": 0.0,
                "alt_m": 35786e3,
            },
            "rx": {
                "name": "ground",
                "lat_deg": 40.0,
                "lon_deg": -74.0,
                "alt_m": 0.0,
            },
        },
        "antenna": {
            "tx": {"model": "parametric"},
            "rx": {"model": "parametric"},
        },
        "rf_chain": {
            "tx_power_w": 100.0,
        },
    }

    def test_simple_rf_chain_still_works(self) -> None:
        """Existing flat config without stages still loads."""
        cfg_data = {**self.MINIMAL_CONFIG}
        cfg_data["rf_chain"] = {
            "tx_power_w": 100.0,
            "tx_losses_db": 2.0,
            "rx_noise_temp_k": 500.0,
        }
        cfg = ProjectConfig.model_validate(cfg_data)
        assert cfg.rf_chain.stages is None
        assert cfg.rf_chain.tx_losses_db == 2.0
        assert cfg.rf_chain.rx_noise_temp_k == 500.0

    def test_config_with_stages_loads(self) -> None:
        cfg_data = {**self.MINIMAL_CONFIG}
        cfg_data["rf_chain"] = {
            "tx_power_w": 100.0,
            "stages": [
                {"name": "LNA", "gain_db": 25.0, "nf_db": 0.8},
                {"name": "Mixer", "gain_db": 10.0, "nf_db": 8.0},
            ],
        }
        cfg = ProjectConfig.model_validate(cfg_data)
        assert cfg.rf_chain.stages is not None
        assert len(cfg.rf_chain.stages) == 2
        assert cfg.rf_chain.stages[0].name == "LNA"

    def test_builder_with_stages(self) -> None:
        """build_link_inputs uses cascaded chain when stages present."""
        from opensatcom.cli.builders import build_link_inputs_from_config

        cfg_data = {**self.MINIMAL_CONFIG}
        cfg_data["rf_chain"] = {
            "tx_power_w": 50.0,
            "stages": [
                {"name": "LNA", "gain_db": 25.0, "nf_db": 1.0},
                {"name": "Filter", "gain_db": -2.0, "nf_db": 2.0},
            ],
        }
        cfg = ProjectConfig.model_validate(cfg_data)
        inputs = build_link_inputs_from_config(cfg)
        # Cascaded noise temp should be computed from stages
        assert inputs.rf_chain.rx_noise_temp_k > 0
        assert inputs.rf_chain.tx_power_w == 50.0
