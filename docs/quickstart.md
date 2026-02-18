# OpenSatCom Quickstart Guide

## Installation

```bash
git clone https://github.com/jman4162/opensatcom.git
cd opensatcom
pip install -e ".[dev]"
```

## 1. First Link Budget

```python
from opensatcom.core.models import *
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.propagation import FreeSpacePropagation
from opensatcom.link.engine import DefaultLinkEngine
from opensatcom.geometry.slant import slant_range_m

satellite = Terminal("GEO-Sat", 0.0, 0.0, 35_786_000.0)
ground = Terminal("Ground", 38.9, -77.0, 0.0, system_noise_temp_k=290.0)

link_inputs = LinkInputs(
    tx_terminal=satellite,
    rx_terminal=ground,
    scenario=Scenario(
        name="Ku-DL", direction="downlink",
        freq_hz=12e9, bandwidth_hz=36e6,
        polarization="RHCP", required_metric="ebn0_db", required_value=5.0,
    ),
    tx_antenna=ParametricAntenna(gain_dbi=36.0),
    rx_antenna=ParametricAntenna(gain_dbi=38.0),
    propagation=FreeSpacePropagation(),
    rf_chain=RFChainModel(tx_power_w=100.0, tx_losses_db=1.5, rx_noise_temp_k=75.0),
)

engine = DefaultLinkEngine()
range_m = slant_range_m(0.0, 35_786_000.0, 30.0)
result = engine.evaluate_snapshot(30.0, 0.0, range_m, link_inputs, PropagationConditions())
print(f"Margin: {result.margin_db:.2f} dB")
```

## 2. Mission Simulation

```bash
opensatcom mission examples/leo_pass.yaml
```

Or via Python:

```python
from opensatcom.world.sim import SimpleWorldSim
from opensatcom.world.providers import PrecomputedTrajectory, StaticEnvironmentProvider

sim = SimpleWorldSim()
result = sim.run(link_inputs, trajectory, OpsPolicy(), env)
print(f"Availability: {result.summary['availability']:.2%}")
```

## 3. Multi-Beam Payload

```python
from opensatcom.payload.beam import Beam
from opensatcom.payload.beamset import BeamSet
from opensatcom.payload.capacity import compute_beam_map

beamset = BeamSet(beams, scenario, propagation, rf_chain)
beam_map = compute_beam_map(beamset, grid_az, grid_el, rx_antenna, rx_terminal, range_m, cond)
print(f"Mean SINR: {beam_map.sinr_db_mean:.2f} dB")
```

## 4. Trade Studies

```python
from opensatcom.trades import RequirementsTemplate, DesignOfExperiments, BatchRunner, extract_pareto_front

req = RequirementsTemplate()
req.add("freq_hz", 10e9, 30e9)
req.add("tx_power_w", 10.0, 200.0)

doe = DesignOfExperiments(req.to_parameter_space())
cases = doe.generate(200, method="lhs")

runner = BatchRunner()
results = runner.run(cases)

pareto = extract_pareto_front(results, "cost", "margin_db")
```

## 5. Visualizations

```python
from opensatcom.viz import plot_link_margin_timeline, plot_pareto_interactive

fig = plot_link_margin_timeline(times_s, margin_db, outages_mask)
fig.show()
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `opensatcom run config.yaml` | Snapshot link evaluation |
| `opensatcom mission config.yaml` | Time-series mission simulation |
| `opensatcom beammap config.yaml` | Multi-beam capacity map |
| `opensatcom doe config.yaml -n 500` | Design of experiments |
| `opensatcom batch cases.parquet` | Batch evaluation |
| `opensatcom pareto results.parquet --x cost --y margin` | Pareto extraction |
| `opensatcom report results.parquet` | Generate HTML report |
