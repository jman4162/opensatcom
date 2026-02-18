"""Shared test fixtures for OpenSatCom."""

import numpy as np
import pytest

from opensatcom.antenna.pam import PamArrayAntenna
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.core.models import (
    LinkInputs,
    RFChainModel,
    Scenario,
    Terminal,
)
from opensatcom.propagation.composite import CompositePropagation
from opensatcom.propagation.fspl import FreeSpacePropagation
from opensatcom.world.providers import PrecomputedPassData


@pytest.fixture
def canonical_terminals() -> tuple[Terminal, Terminal]:
    """Canonical TX (satellite) and RX (user terminal) pair."""
    tx = Terminal("sat", 0.0, 0.0, 550e3)
    rx = Terminal("ut", 47.6062, -122.3321, 50.0, system_noise_temp_k=500.0)
    return tx, rx


@pytest.fixture
def canonical_scenario() -> Scenario:
    """Canonical downlink scenario at 19.7 GHz."""
    return Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)


@pytest.fixture
def canonical_link_inputs(
    canonical_terminals: tuple[Terminal, Terminal],
    canonical_scenario: Scenario,
) -> LinkInputs:
    """Canonical link inputs matching spec Hello World."""
    tx, rx = canonical_terminals
    tx_ant = PamArrayAntenna(nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5)
    rx_ant = ParametricAntenna(gain_dbi=35.0)
    prop = CompositePropagation([FreeSpacePropagation()])
    rf = RFChainModel(tx_power_w=200.0, tx_losses_db=2.0, rx_noise_temp_k=500.0)
    return LinkInputs(tx, rx, canonical_scenario, tx_ant, rx_ant, prop, rf)


@pytest.fixture
def synthetic_pass_data() -> PrecomputedPassData:
    """Synthetic 20-step satellite pass."""
    n = 20
    times = np.arange(n, dtype=float)
    elev = np.concatenate([
        np.linspace(5.0, 80.0, n // 2),
        np.linspace(80.0, 5.0, n // 2),
    ])
    az = np.zeros(n)
    range_m = np.concatenate([
        np.linspace(1500e3, 550e3, n // 2),
        np.linspace(550e3, 1500e3, n // 2),
    ])
    return PrecomputedPassData(times, elev, az, range_m)
