# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenSatCom is a professional-grade, open-source Python toolkit for satellite communications engineering. It maps **antenna + RF chain + propagation + mission time-series → link margin & capacity**, with reproducible, trade-study-ready outputs.

OpenSatCom is a **domain + glue layer** — it does not reimplement engines. It wraps:
- **PAM** (phased-array-modeling): fast phased-array pattern synthesis
- **PAS** (phased-array-systems): requirements-driven workflows, DOE/Pareto trades
- **EdgeFEM** (edgefem): optional coupling-aware element-level fidelity
- **APAB** (agentic-phased-array-builder): optional agent orchestration

## Build & Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run a single test
pytest tests/test_file.py::test_name -v

# Type checking
mypy src/opensatcom/

# Linting
ruff check src/ tests/

# CLI entry points
opensatcom run config.yaml          # snapshot link evaluation
opensatcom mission config.yaml      # time-series mission simulation
opensatcom beammap config.yaml      # multi-beam capacity map
opensatcom doe config.yaml -n 500 --method lhs   # design of experiments
opensatcom batch cases.parquet --parallel
opensatcom report results.parquet --format html
opensatcom pareto results.parquet --x cost_usd --y throughput_p50
```

## Architecture (Module Layout)

```
src/opensatcom/
├── core/          # Datamodels (Terminal, Scenario, etc.), units, constants, serialization
├── antenna/       # PAM wrappers + EdgeFEM ingestion adapters
├── rf/            # RF chain models (tx power, losses, noise temp cascades)
├── propagation/   # FSPL, ITU-R P.618 rain, P.676 gas, scintillation, composite
├── geometry/      # Slant range, elevation/azimuth, pointing, optional Doppler
├── modem/         # DVB-S2 ModCod table, analytic BER curves, ACM hysteresis policy
├── link/          # Snapshot link budget engine, margin computation, throughput
├── payload/       # BeamSet, BeamMap, multi-beam interference
├── world/         # WorldSim Tier 1/2/3, traffic models, schedulers, handover
├── trades/        # DOE (LHS/factorial/random), batch runner, Pareto extraction
├── viz/           # Plotly interactive + Seaborn statistical visualizations
├── reports/       # HTML report generation with optional Plotly embeds
├── io/            # Artifact I/O (parquet, json, yaml, hdf5)
└── cli/           # CLI entrypoints (run, mission, beammap, doe, batch, pareto)
```

## Key Design Patterns

**Protocol-based interfaces** — Public seams use `typing.Protocol` + frozen dataclasses. Key protocols: `AntennaModel`, `PropagationModel`, `PerformanceCurve`, `ACMPolicy`, `LinkEngine`, `TrajectoryProvider`, `EnvironmentProvider`.

**Plugin architecture** — Propagation models registered via builders. FSPL, ITU-R rain (P.618), gas (P.676), and scintillation are built-in. Config types: `"fspl"`, `"itur_rain"/"rain"`, `"itur_gas"/"gas"`, `"scintillation"`.

**Composite propagation** — `CompositePropagation` sums multiple loss components (FSPL + atmospheric + rain + scintillation). Losses sum in dB; noise/interference sum in linear domain then convert to dB.

**Tiered world model** — Tier 1: single satellite ↔ terminal. Tier 2: multi-sat handover. Tier 3: network traffic with proportional fair / round-robin scheduling.

**DVB-S2 modem** — 28 built-in ModCods with analytic BER curves. `get_dvbs2_modcod_table()` and `get_dvbs2_performance_curves()` provide defaults. Config-driven via `modem.enabled: true`.

**Trade studies** — `RequirementsTemplate` → `DesignOfExperiments` (LHS via scipy) → `BatchRunner` → `extract_pareto_front`. All wired via CLI.

**Visualizations** — `viz/` module with Plotly interactive (timeline, heatmaps, trades, constellation) and Seaborn statistical (distributions, waterfalls, availability heatmaps).

**Run artifacts** — Every run produces `config_snapshot.yaml`, `results.parquet`, and an `artifacts/` folder (plots, link tables, patterns). Deterministic outputs for given configs.

## Dependencies

Core: `numpy`, `pandas`, `pyyaml`, `pydantic`, `matplotlib`, `pyarrow`, `scipy`, `plotly`, `seaborn`

## Unit & Coordinate Conventions

- Internal representation: **SI units** (Hz, meters, seconds, Kelvin, Watts)
- dB-space fields are explicitly named: `eirp_dbw`, `cn0_dbhz`, `gt_dbk`, `margin_db`
- Helper utilities: `lin_to_db10`, `db10_to_lin`, `lin_to_db20`, `db20_to_lin`, `w_to_dbw`, `dbw_to_w`
- Coordinates: local tangent plane (ENU) at terminal; satellite direction in az/el relative to terminal
- ECI/ECEF conversion handled in plugin layer (not core)

## Configuration

Project config is YAML-driven with sections: `project`, `scenario`, `terminals`, `antenna`, `rf_chain`, `propagation`, `modem`, `world`, `trades`, `reports`, `payload`.

## Testing Strategy

- **Golden test vectors** in `tests/golden/`: propagation, modem, network simulation
- **Unit tests** in `tests/unit/`: all modules
- **Integration tests** in `tests/integration/`: CLI commands
- Test markers: `integration`, `golden`

## Roadmap

- **P0 (v0.1)** ✅: Snapshot link engine, FSPL, ModCod/ACM, WorldSim Tier 1, HTML reports
- **P1 (v0.2)** ✅: Multi-beam payload, interference model, capacity maps
- **P2 (v0.3)** ✅: EdgeFEM coupling, multi-sat handover, cascaded RF chain
- **P3 (v0.4)** ✅: ITU-R propagation, DVB-S2, trades module, network traffic Tier 3, CI/CD, Plotly/Seaborn viz, Jupyter tutorials

## Git & GitHub

- All commits must be authored by **John Hodge (jman4162)**: `git config user.name "John Hodge"`, `git config user.email "jah70@vt.edu"`
- The active `gh` account must be **jman4162** before pushing. Switch with: `gh auth switch --user jman4162`
