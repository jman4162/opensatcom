"""Batch runner for evaluating DOE parameter cases."""

from __future__ import annotations

from typing import Any

import pandas as pd


class BatchRunner:
    """Evaluates a DataFrame of parameter cases against a base config.

    Each row in the cases DataFrame represents a parameter combination.
    The runner modifies the base config for each case, evaluates a link budget,
    and collects results.

    Parameters
    ----------
    base_config_path : str | None
        Path to base YAML config. If None, a minimal default is used.
    """

    def __init__(self, base_config_path: str | None = None) -> None:
        self._base_config_path = base_config_path

    def run(
        self,
        cases_df: pd.DataFrame,
        base_config: dict[str, Any] | None = None,
        parallel: bool = False,
    ) -> pd.DataFrame:
        """Run batch evaluation.

        Parameters
        ----------
        cases_df : pd.DataFrame
            Parameter combinations. Columns map to config fields.
        base_config : dict | None
            Base configuration dict to override with case parameters.
        parallel : bool
            Use multiprocessing for parallel evaluation.
        """
        if parallel:
            return self._run_parallel(cases_df, base_config)
        return self._run_sequential(cases_df, base_config)

    def _evaluate_single(
        self, case: dict[str, float], base_config: dict[str, Any] | None
    ) -> dict[str, float]:
        """Evaluate a single parameter case."""
        from opensatcom.core.models import PropagationConditions
        from opensatcom.geometry.slant import slant_range_m
        from opensatcom.link.engine import DefaultLinkEngine

        # Build link inputs by merging case params into base config
        if base_config is not None:
            from opensatcom.cli.builders import build_link_inputs_from_config
            from opensatcom.io.config_loader import ProjectConfig

            merged = _deep_merge(base_config, case)
            cfg = ProjectConfig.model_validate(merged)
            link_inputs = build_link_inputs_from_config(cfg)
        else:
            # Minimal evaluation using case parameters directly
            from opensatcom.antenna.parametric import ParametricAntenna
            from opensatcom.core.models import (
                LinkInputs,
                RFChainModel,
                Scenario,
                Terminal,
            )
            from opensatcom.propagation.fspl import FreeSpacePropagation

            freq_hz = case.get("freq_hz", 12e9)
            tx_power_w = case.get("tx_power_w", 100.0)
            tx_gain_dbi = case.get("tx_gain_dbi", 30.0)
            rx_gain_dbi = case.get("rx_gain_dbi", 30.0)
            bandwidth_hz = case.get("bandwidth_hz", 36e6)
            required_ebn0_db = case.get("required_ebn0_db", 10.0)

            link_inputs = LinkInputs(
                tx_terminal=Terminal("tx", 0.0, 0.0, 35786e3),
                rx_terminal=Terminal("rx", 0.0, 0.0, 0.0, system_noise_temp_k=290.0),
                scenario=Scenario(
                    name="batch",
                    direction="downlink",
                    freq_hz=freq_hz,
                    bandwidth_hz=bandwidth_hz,
                    polarization="RHCP",
                    required_metric="ebn0_db",
                    required_value=required_ebn0_db,
                ),
                tx_antenna=ParametricAntenna(gain_dbi=tx_gain_dbi),
                rx_antenna=ParametricAntenna(gain_dbi=rx_gain_dbi),
                propagation=FreeSpacePropagation(),
                rf_chain=RFChainModel(
                    tx_power_w=tx_power_w,
                    tx_losses_db=0.0,
                    rx_noise_temp_k=0.0,
                ),
            )

        elev_deg = case.get("elev_deg", 30.0)
        range_m = slant_range_m(
            link_inputs.rx_terminal.alt_m,
            link_inputs.tx_terminal.alt_m,
            elev_deg,
        )

        engine = DefaultLinkEngine()
        out = engine.evaluate_snapshot(
            elev_deg=elev_deg,
            az_deg=0.0,
            range_m=range_m,
            inputs=link_inputs,
            cond=PropagationConditions(),
        )

        result = dict(case)
        result["eirp_dbw"] = out.eirp_dbw
        result["cn0_dbhz"] = out.cn0_dbhz
        result["ebn0_db"] = out.ebn0_db
        result["margin_db"] = out.margin_db
        return result

    def _run_sequential(
        self, cases_df: pd.DataFrame, base_config: dict[str, Any] | None
    ) -> pd.DataFrame:
        results = []
        for _, row in cases_df.iterrows():
            case: dict[str, float] = {str(k): v for k, v in row.to_dict().items()}
            results.append(self._evaluate_single(case, base_config))
        return pd.DataFrame(results)

    def _run_parallel(
        self, cases_df: pd.DataFrame, base_config: dict[str, Any] | None
    ) -> pd.DataFrame:
        from concurrent.futures import ProcessPoolExecutor

        cases = [row.to_dict() for _, row in cases_df.iterrows()]
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(_eval_wrapper, [(c, base_config) for c in cases]))
        return pd.DataFrame(results)


def _eval_wrapper(args: tuple[dict[str, float], dict[str, Any] | None]) -> dict[str, float]:
    """Top-level wrapper for multiprocessing (must be picklable)."""
    case, base_config = args
    runner = BatchRunner()
    return runner._evaluate_single(case, base_config)


def _deep_merge(base: dict[str, Any], overrides: dict[str, float]) -> dict[str, Any]:
    """Merge case parameter overrides into a base config dict.

    Maps flat parameter names to nested config paths using conventions:
    - "freq_hz" -> scenario.freq_hz
    - "tx_power_w" -> rf_chain.tx_power_w
    """
    import copy

    result = copy.deepcopy(base)

    param_map = {
        "freq_hz": ("scenario", "freq_hz"),
        "bandwidth_hz": ("scenario", "bandwidth_hz"),
        "tx_power_w": ("rf_chain", "tx_power_w"),
        "tx_losses_db": ("rf_chain", "tx_losses_db"),
        "rx_noise_temp_k": ("rf_chain", "rx_noise_temp_k"),
    }

    for key, value in overrides.items():
        if key in param_map:
            section, field = param_map[key]
            if section in result:
                result[section][field] = value
        # Other keys are passed through as-is in the result

    return result
