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
├── propagation/   # FSPL built-in + plugin adapters (ITU-R rain/gas/scintillation)
├── geometry/      # Slant range, elevation/azimuth, pointing, optional Doppler
├── modem/         # ModCod tables, performance curves, ACM hysteresis policy
├── link/          # Snapshot link budget engine, margin computation, throughput
├── payload/       # BeamSet, BeamMap, multi-beam interference (P1)
├── world/         # Mission/ops time-series simulation engine
├── trades/        # PAS integration helpers (DOE, Pareto, requirements templates)
├── reports/       # HTML/PDF report generation, plots
├── io/            # Artifact I/O (parquet, json, yaml, hdf5)
└── cli/           # CLI entrypoints
```

## Key Design Patterns

**Protocol-based interfaces** — Public seams use `typing.Protocol` + frozen dataclasses. Key protocols: `AntennaModel`, `PropagationModel`, `PerformanceCurve`, `ACMPolicy`, `LinkEngine`, `TrajectoryProvider`, `EnvironmentProvider`.

**Plugin architecture** — Propagation models and orbit trajectory providers are registered via Python entry points (e.g., `opensatcom.propagation_models`). FSPL is built-in; ITU-R rain/gas are plugin adapters.

**Composite propagation** — `CompositePropagation` sums multiple loss components (FSPL + atmospheric + rain + scintillation). Losses sum in dB; noise/interference sum in linear domain then convert to dB.

**Tiered world model** — Tier 1 (P0): single satellite ↔ terminal time-series. Tier 2 (P1): multi-sat handover heuristic. Tier 3 (deferred): network traffic.

**Run artifacts** — Every run produces `config_snapshot.yaml`, `results.parquet`, and an `artifacts/` folder (plots, link tables, patterns). Deterministic outputs for given configs.

## Unit & Coordinate Conventions

- Internal representation: **SI units** (Hz, meters, seconds, Kelvin, Watts)
- dB-space fields are explicitly named: `eirp_dbw`, `cn0_dbhz`, `gt_dbk`, `margin_db`
- Helper utilities: `lin_to_db10`, `db10_to_lin`, `lin_to_db20`, `db20_to_lin`, `w_to_dbw`, `dbw_to_w`
- Coordinates: local tangent plane (ENU) at terminal; satellite direction in az/el relative to terminal
- ECI/ECEF conversion handled in plugin layer (not core)

## Configuration

Project config is YAML-driven with sections: `project`, `scenario`, `terminals`, `antenna`, `rf_chain`, `propagation`, `modem`, `world`, `trades`, `reports`. See `background_information.md` section 18 for the full schema.

## Testing Strategy

- **Golden test vectors** in `tests/golden/`: snapshot link budgets (FSPL), rain loss, mission pass simulation, ModCod/ACM selection
- **Regression tests**: freeze representative configs in `examples/`, re-run in CI; metric drift requires explicit baseline update PR
- **Numerical stability**: avoid subtractive cancellation in dB conversions; sum noise/interference in linear domain
- Test markers: `integration`, `golden`

## Roadmap

- **P0 (v0.1)**: Snapshot link engine, composite propagation (FSPL), ModCod/ACM, WorldSim Tier 1, HTML reports, golden tests + CI
- **P1 (v0.2)**: Multi-beam payload (BeamSet/BeamMap), interference model, capacity maps
- **P2 (v0.3+)**: EdgeFEM coupling ingestion end-to-end, multi-sat handover, richer RF chain modeling

## Git & GitHub

- All commits must be authored by **John Hodge (jman4162)**: `git config user.name "John Hodge"`, `git config user.email "jhodge007@gmail.com"`
- The active `gh` account must be **jman4162** before pushing. Switch with: `gh auth switch --user jman4162`
