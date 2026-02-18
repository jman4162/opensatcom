# OpenSatCom

[![CI](https://github.com/jman4162/opensatcom/actions/workflows/ci.yml/badge.svg)](https://github.com/jman4162/opensatcom/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/opensatcom.svg)](https://pypi.org/project/opensatcom/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/jman4162/opensatcom/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://jman4162.github.io/opensatcom/)

**Professional-grade, open-source Python toolkit for satellite communications engineering.**

Maps **antenna + RF chain + propagation + mission time-series** to **link margin & capacity**, with reproducible, trade-study-ready outputs.

---

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

## Quick Install

```bash
pip install opensatcom
```

See [Installation](getting-started/installation.md) for extras and development setup.

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

## Design Principles

- **Protocol-based interfaces** — Public seams use `typing.Protocol` + frozen dataclasses
- **Plugin architecture** — Propagation models registered via builders
- **SI units internally** — dB-space fields explicitly named (`eirp_dbw`, `cn0_dbhz`)
- **Deterministic outputs** — Every run produces `config_snapshot.yaml`, `results.parquet`, and an `artifacts/` folder

## License

MIT License. See [LICENSE](https://github.com/jman4162/opensatcom/blob/main/LICENSE) for details.
