# OpenSatCom

[![CI](https://github.com/jman4162/opensatcom/actions/workflows/ci.yml/badge.svg)](https://github.com/jman4162/opensatcom/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/opensatcom.svg)](https://pypi.org/project/opensatcom/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/type--checked-mypy-blue.svg)](https://mypy-lang.org/)

Professional-grade, open-source Python toolkit for satellite communications engineering.

Maps **antenna + RF chain + propagation + mission time-series** to **link margin & capacity**, with reproducible, trade-study-ready outputs.

## Features

- **Snapshot link budgets** — EIRP, G/T, C/N0, Eb/N0, margin in one call
- **Composite propagation** — FSPL + ITU-R P.618 rain + P.676 gas + scintillation
- **DVB-S2 modem** — 28 built-in ModCods, analytic BER curves, hysteresis ACM
- **Multi-beam payload** — BeamSet, SINR/C(N+I) maps, interference modeling
- **Mission simulation** — Tier 1 (single-sat), Tier 2 (multi-sat handover), Tier 3 (network traffic)
- **Trade studies** — DOE (LHS/factorial/random), batch evaluation, Pareto extraction
- **Beautiful visualizations** — Plotly interactive + Seaborn statistical plots
- **HTML reports** — Standalone reports with embedded interactive charts
- **CLI interface** — `opensatcom run`, `mission`, `beammap`, `doe`, `batch`, `pareto`

## Installation

```bash
pip install opensatcom
```

For development:
```bash
pip install -e ".[dev]"
```

For Jupyter notebooks:
```bash
pip install -e ".[notebooks]"
```

## Quickstart

```python
from opensatcom.core.models import *
from opensatcom.antenna.parametric import ParametricAntenna
from opensatcom.propagation import FreeSpacePropagation
from opensatcom.link.engine import DefaultLinkEngine
from opensatcom.geometry.slant import slant_range_m

# Define terminals
satellite = Terminal("GEO-Sat", 0.0, 0.0, 35_786_000.0)
ground = Terminal("Ground", 38.9, -77.0, 0.0, system_noise_temp_k=290.0)

# Build link inputs
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

# Evaluate
engine = DefaultLinkEngine()
range_m = slant_range_m(0.0, 35_786_000.0, 30.0)
result = engine.evaluate_snapshot(30.0, 0.0, range_m, link_inputs, PropagationConditions())
print(f"Margin: {result.margin_db:.2f} dB")
```

## Architecture

```
src/opensatcom/
├── core/          # Datamodels, protocols, units, constants
├── antenna/       # PAM wrappers, parametric, cosine, coupling
├── rf/            # RF chain, cascaded stages
├── propagation/   # FSPL, ITU-R rain/gas/scintillation, composite
├── geometry/      # Slant range, elevation/azimuth
├── modem/         # DVB-S2 ModCods, analytic BER, ACM policy
├── link/          # Snapshot link budget engine
├── payload/       # BeamSet, BeamMap, multi-beam interference
├── world/         # WorldSim Tier 1/2/3, traffic, schedulers
├── trades/        # DOE, batch runner, Pareto extraction
├── viz/           # Plotly + Seaborn visualizations
├── reports/       # HTML report generation
├── io/            # Artifact I/O (parquet, yaml, json)
└── cli/           # CLI entry points
```

## CLI Usage

```bash
# Snapshot link evaluation
opensatcom run config.yaml

# Time-series mission simulation
opensatcom mission config.yaml

# Multi-beam capacity map
opensatcom beammap config.yaml

# Design of experiments
opensatcom doe config.yaml -n 500 --method lhs

# Batch evaluation
opensatcom batch cases.parquet --parallel

# Pareto extraction
opensatcom pareto results.parquet --x cost_usd --y throughput_p50

# Generate report
opensatcom report results.parquet --format html
```

## Tutorial Notebooks

| Notebook | Topic | Colab |
|----------|-------|-------|
| `01_quickstart.ipynb` | End-to-end snapshot link budget | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/01_quickstart.ipynb) |
| `02_mission_simulation.ipynb` | Time-series mission simulation | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/02_mission_simulation.ipynb) |
| `03_multibeam_payload.ipynb` | Multi-series capacity analysis | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/03_multibeam_payload.ipynb) |
| `04_propagation_models.ipynb` | Propagation model comparison | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/04_propagation_models.ipynb) |
| `05_trade_studies.ipynb` | DOE + Pareto workflow | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/05_trade_studies.ipynb) |

## Testing

```bash
pytest tests/ -v              # All tests
pytest tests/ -m golden       # Golden regression tests only
pytest tests/ -m integration  # Integration tests only
ruff check src/ tests/        # Lint
mypy src/opensatcom/          # Type check
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## Citation

If you use OpenSatCom in your research or publications, please cite:

```bibtex
@software{opensatcom,
  author       = {Hodge, John},
  title        = {OpenSatCom: Open-Source Satellite Communications Engineering Toolkit},
  year         = {2025},
  publisher    = {GitHub},
  url          = {https://github.com/jman4162/opensatcom},
  version      = {0.4.0},
  license      = {MIT}
}
```

## License

MIT License. See [LICENSE](LICENSE) for details.
