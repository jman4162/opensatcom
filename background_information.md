```markdown
# OpenSatCom (working name): Professional-Grade Open-Source Python SatCom Engineering Toolkit
**Antenna + RF chain + propagation + mission time-series → link margin & capacity, reproducible and trade-study ready.**

Built on top of:
- **Phased-Array-Antenna-Model (PAM)**: fast phased-array pattern synthesis, impairments, visualization
  - https://github.com/jman4162/Phased-Array-Antenna-Model
- **phased-array-systems (PAS)**: requirements-driven system framework, DOE/Pareto, CLI/reporting patterns
  - https://github.com/jman4162/phased-array-systems
- **EdgeFEM**: higher-fidelity element/coupling modeling, unit-cell → coupling/pattern artifacts
  - https://github.com/jman4162/EdgeFEM
- **agentic-phased-array-builder (APAB)** (optional): agent orchestration for “end-to-end” pipelines
  - https://github.com/jman4162/agentic-phased-array-builder

---

## 1. Executive Summary Pitch (copy/paste)

**OpenSatCom** is a professional-grade, open-source Python toolkit for satellite communications engineering—designed for antenna and system engineers who need to connect **phased-array design choices** to **end-to-end link performance and operational outcomes**.

OpenSatCom composes best-in-class engines you already maintain:
- **PAM** for fast, realistic phased-array patterns (scan loss, quantization, failures, tapering, visualization).
- **PAS** for requirements-first workflows, reproducible configs, and large-scale DOE/Pareto trade studies.
- **EdgeFEM** for optional coupling-aware and element-level fidelity that drives array performance.
- **APAB** to optionally enable agentic “design loops” that run full pipelines automatically.

OpenSatCom adds the missing SatCom domain layer:
- SatCom-native **link budgets** (UL/DL), **availability** and **time-series mission simulation**
- **Propagation** plugins (free-space + ITU-R-style models via adapters)
- **ModCod / ACM abstraction** for realistic throughput instead of “Shannon-only”
- **Multi-beam payload** analysis: beam maps → C/N₀ → throughput and interference
- Turnkey, reproducible **engineering reports** (link breakdown tables, margin vs time, capacity distributions)

**Outcome:** Engineers stop debating “pretty patterns” and start answering:
> *Does this design meet availability? What throughput is delivered over a day of operations? What’s the cheapest architecture that closes the link with margin under rain + scan limits + impairments?*

---

## 2. Product Goals, Non-Goals, and “Professional-Grade” Definition

### 2.1 Goals
1. Provide a SatCom-focused domain layer that maps:  
   **antenna + RF chain + propagation + geometry + ops policy → link/capacity metrics**
2. Enable **multi-fidelity** modeling:
   - array-factor only (fast, early trades)
   - coupling-aware (EdgeFEM ingestion)
   - time-series mission evaluation (ops realism)
3. Keep everything **reproducible**:
   - versioned configs
   - deterministic seeds where applicable
   - artifact snapshots
4. Be **trade-study ready**:
   - standardized metric outputs
   - DOE batching
   - Pareto extraction
   - report generation (PAS-style)

### 2.2 Non-Goals (v0.x)
- Full constellation/network simulator (routing, ISL scheduling, traffic engineering)
- Bit-level PHY simulation (LDPC decoding Monte Carlo, waveform impairments)
- Full regulatory workflow automation (support outputs like PFD, EIRP density, but not filing workflows)

### 2.3 “Professional-Grade” Requirements
- Clear model assumptions and unit conventions
- Golden test vectors and regression tests
- CI (lint, type-check, unit tests, docs build)
- Stable public APIs (semver)
- Deterministic outputs for given configs
- Run artifacts: results tables + link breakdown + plots + config snapshot

---

## 3. Target Users and Use Cases

### 3.1 Users
- Antenna/payload engineers: array sizing, scan limits, coupling impacts, sidelobes
- RF/system engineers: cascaded NF/power, EIRP/G/T, link closure, availability
- Algorithm engineers: beamforming, multi-beam allocation, nulling, ACM policies

### 3.2 Primary Use Cases (MVP)
1. **Single snapshot** link closure vs elevation (UL/DL)
2. **Time-series mission**: pass/day simulation → margin(t), throughput(t), outage minutes
3. **Trade study**: array size vs RF power vs cost vs availability → Pareto set
4. **Sensitivity studies**: quantization, failures, coupling, pointing error, scan loss
5. **Multi-beam payload**: beamset → capacity map, interference budgets

---

## 4. Architectural Approach (Composition Layer)

OpenSatCom is intentionally a **domain + glue layer**:
- PAM/PAS/EdgeFEM/APAB remain the engines.
- OpenSatCom defines SatCom-specific datamodels, propagation/mission abstractions, ModCod abstraction, and standardized outputs.

### 4.1 Top-Level Module Layout
```

opensatcom/
**init**.py
core/             # datamodels, units, constants, serialization
antenna/          # PAM wrappers + EdgeFEM ingestion adapters
rf/               # RF chain models, budgets, cascades
propagation/      # FSPL + plugin adapters for atmospheric/rain losses
geometry/         # slant range, elevation/azimuth, pointing, doppler (optional)
modem/            # ModCod tables, performance curves, ACM policy
link/             # link budget engine, margins, throughput estimators
payload/          # beamsets, multi-beam maps, interference
world/            # mission/ops simulation engine (time series)
trades/           # PAS integration helpers (DOE, Pareto, requirements)
reports/          # report generation templates (HTML/PDF), plots
io/               # reading/writing artifacts (parquet, json, yaml, hdf5)
cli/              # opensatcom command line entrypoints
tests/
docs/
examples/

````

### 4.2 Dependency Policy
- Required dependencies should be minimal: `numpy`, `scipy` (if needed), `pandas`, `pyyaml`, `pydantic` (optional), `matplotlib` (or plotly optional), `pyarrow` for parquet.
- Optional extras:
  - `itur` adapter for ITU-R style propagation models
  - `skyfield`/`sgp4`/`poliastro` adapter for orbit propagation (plugin)
  - `reporting` extras for HTML/PDF generation

---

## 5. Core Conventions: Units, Coordinates, and Data Integrity

### 5.1 Units
- Default internal representation: **SI units** (Hz, meters, seconds, Kelvin, Watts).
- dB-space values: clearly named fields (e.g., `eirp_dbw`, `cn0_dbhz`, `gt_dbk`).
- Provide helper utilities for dB conversions:
  - `lin_to_db10`, `db10_to_lin`, `lin_to_db20`, `db20_to_lin`
  - `w_to_dbw`, `dbw_to_w`

### 5.2 Coordinate Frames
- Support minimal geometry without forcing a full astrodynamics stack:
  - local tangent plane at terminal (ENU)
  - satellite direction in az/el relative to terminal
- If orbit plugins are used:
  - ECI/ECEF conversion handled in plugin layer
  - OpenSatCom consumes standardized time-tagged states

### 5.3 Serialization
- Every run produces:
  - `config_snapshot.yaml`
  - `results.parquet` (row per case or per time-step)
  - `artifacts/` folder (plots, link tables, patterns, beam maps)

---

## 6. Public API Design (Stable Interfaces)

Use `typing.Protocol` + dataclasses for the “public seam” objects.

### 6.1 Core Datamodels (Pydantic optional)
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Protocol
import numpy as np

@dataclass(frozen=True)
class Terminal:
    name: str
    lat_deg: float
    lon_deg: float
    alt_m: float
    system_noise_temp_k: Optional[float] = None
    misc: Optional[Dict[str, Any]] = None

@dataclass(frozen=True)
class Scenario:
    name: str
    direction: str          # "uplink" or "downlink"
    freq_hz: float
    bandwidth_hz: float
    polarization: str        # e.g. "RHCP", "LHCP", "H", "V"
    required_metric: str     # "ebn0_db", "cn0_dbhz", "throughput_mbps"
    required_value: float
    misc: Optional[Dict[str, Any]] = None
````

### 6.2 Antenna Model Interface (wrap PAM)

```python
class AntennaModel(Protocol):
    def gain_dbi(self, theta_deg: np.ndarray, phi_deg: np.ndarray, f_hz: float) -> np.ndarray:
        ...

    def eirp_dbw(self, theta_deg: float, phi_deg: float, f_hz: float, tx_power_w: float) -> float:
        ...
```

Implementations:

* `PamArrayAntenna(...)`
* `CouplingAwareAntenna(...)` (ingests EdgeFEM outputs)

### 6.3 Propagation Interface (plugin-based)

```python
@dataclass(frozen=True)
class PropagationConditions:
    availability_target: Optional[float] = None   # e.g., 0.999
    rain_rate_mm_per_hr: Optional[float] = None
    climate_region: Optional[str] = None
    misc: Optional[Dict[str, Any]] = None

class PropagationModel(Protocol):
    def total_path_loss_db(self, f_hz: float, elev_deg: float, range_m: float,
                           cond: PropagationConditions) -> float:
        ...
```

### 6.4 Modem/ModCod Abstraction (no bit-level sim required)

```python
@dataclass(frozen=True)
class ModCod:
    name: str
    bits_per_symbol: float
    code_rate: float
    rolloff: float = 0.2
    pilot_overhead: float = 0.0
    impl_margin_db: float = 0.0

    def net_spectral_eff_bps_per_hz(self) -> float:
        return self.bits_per_symbol * self.code_rate * (1 - self.pilot_overhead) / (1 + self.rolloff)

class PerformanceCurve(Protocol):
    def bler(self, ebn0_db: float) -> float: ...
    def required_ebn0_db(self, target_bler: float) -> float: ...

class ACMPolicy(Protocol):
    def select_modcod(self, ebn0_db: float, t_s: float) -> ModCod: ...
```

### 6.5 Link Engine Interface

```python
@dataclass(frozen=True)
class LinkInputs:
    tx_terminal: Terminal
    rx_terminal: Terminal
    scenario: Scenario
    tx_antenna: AntennaModel
    rx_antenna: AntennaModel
    propagation: PropagationModel
    rf_chain: "RFChainModel"
    modem: Optional["ModemModel"] = None

@dataclass(frozen=True)
class LinkOutputs:
    eirp_dbw: float
    gt_dbk: float
    path_loss_db: float
    cn0_dbhz: float
    ebn0_db: float
    margin_db: float
    throughput_mbps: Optional[float] = None
    breakdown: Optional[Dict[str, float]] = None

class LinkEngine(Protocol):
    def evaluate_snapshot(self, elev_deg: float, az_deg: float, range_m: float,
                          inputs: LinkInputs, cond: PropagationConditions) -> LinkOutputs:
        ...
```

---

## 7. Antenna Module Spec (PAM + EdgeFEM)

### 7.1 PAM Wrapper Requirements

* Define an adapter that takes:

  * array geometry (Nx, Ny, dx, dy)
  * element pattern model (isotropic or imported)
  * beam steering / weights
  * impairments: phase quantization, amplitude quantization, failures, jitter
* Output:

  * gain patterns
  * scan loss, sidelobe metrics
  * polarization mismatch loss if available

### 7.2 EdgeFEM Ingestion Requirements

Support ingestion of artifacts produced by EdgeFEM runs:

* Active element patterns vs scan angle/frequency (or gridded patterns)
* Coupling matrices (S-parameters / Z matrices)
* Effective embedded element pattern approximations

Minimum ingestion formats:

* `*.sNp` Touchstone for coupling
* `*.npz` for precomputed pattern/coupling grids
* JSON/YAML metadata for frequency grids and definitions

### 7.3 Antenna Outputs Needed by Link Engine

* Directional gain (dBi) as a function of az/el (or theta/phi)
* Optional:

  * polarization basis vectors
  * boresight definition
  * maximum scan angle constraints
  * pointing error sensitivity model (gain degradation vs pointing offset)

---

## 8. RF Chain Module Spec

### 8.1 RFChainModel

Provide a standardized cascade model for:

* TX chain: DAC/IF → upconversion → PA → losses → antenna feed
* RX chain: antenna feed → LNA → downconversion → ADC → demod

Minimum parameters:

* TX power at PA output (W)
* TX losses (dB) (feed, insertion, backoff)
* RX noise temperature or NF chain
* Optional: linearity metrics (IIP3) for interference sensitivity

API:

```python
@dataclass(frozen=True)
class RFChainModel:
    tx_power_w: float
    tx_losses_db: float
    rx_noise_temp_k: float
    misc: Optional[Dict[str, Any]] = None

    def effective_tx_power_w(self) -> float:
        ...

    def system_temp_k(self, base_temp_k: float) -> float:
        ...
```

---

## 9. Propagation Module Spec

### 9.1 Built-in Models

* `FreeSpacePropagation`: FSPL + optional fixed margins
* `CompositePropagation`: sum of multiple components:

  * FSPL
  * atmospheric gas absorption (plugin)
  * rain attenuation (plugin)
  * scintillation (plugin)
  * pointing loss (may live in geometry or payload)

### 9.2 Plugin Architecture

Use Python entry points:

* `opensatcom.propagation_models`
* each plugin registers a class implementing `PropagationModel`

---

## 10. Geometry Module Spec

### 10.1 Snapshot Geometry

Given:

* terminal lat/lon/alt
* satellite state OR direct az/el/range
  Compute:
* slant range (m)
* elevation (deg)
* azimuth (deg)
* scan angle relative to antenna boresight
* optional Doppler (Hz) if velocity is provided

### 10.2 Time-Series Geometry (consumed by World Model)

Standardized state format:

```python
@dataclass(frozen=True)
class StateECEF:
    t_s: float
    r_m: np.ndarray  # shape (3,)
    v_mps: Optional[np.ndarray] = None
```

World model can use:

* a plugin `TrajectoryProvider` to generate `StateECEF` for satellites
* static terminals produce constant states (ECEF position fixed)

---

## 11. Modem Module Spec (ModCod + ACM)

### 11.1 ModemModel

A ModemModel maps (Eb/N0, bandwidth) to throughput.

Core components:

* ModCod set (list)
* performance curves (required Eb/N0 at target BLER)
* ACM policy with hysteresis
* throughput calculator

API:

```python
@dataclass(frozen=True)
class ModemModel:
    modcods: List[ModCod]
    curves: Dict[str, PerformanceCurve]  # keyed by ModCod.name
    target_bler: float
    acm_policy: ACMPolicy

    def throughput_mbps(self, ebn0_db: float, bandwidth_hz: float, t_s: float) -> Dict[str, float]:
        """
        Returns dict containing throughput_mbps, selected_modcod, spectral_eff, bler_est
        """
        ...
```

### 11.2 Built-in Curves

Provide two options:

1. **Table-based** curves: user supplies CSV/JSON of Eb/N0 vs BLER or required Eb/N0
2. **Simple analytic** curves: logistic fit parameters (for quick demos), clearly labeled “approximate”

### 11.3 Implementation Margins

Support:

* implementation margin (dB)
* fading margin (dB) (distinct from propagation losses)
* ACM hysteresis to avoid “flapping”

---

## 12. Link Module Spec (Snapshot Engine)

### 12.1 Link Budget Computation

At minimum compute:

* EIRP (dBW)
* RX antenna gain (dBi)
* Path loss (dB) and component breakdown
* C/N0 (dB-Hz)
* Eb/N0 (dB)
* Margin relative to requirement
* Throughput if modem model is enabled

### 12.2 Link Breakdown Table

Return `breakdown` dict with named terms:

* `tx_power_dbw`
* `tx_losses_db`
* `tx_antenna_gain_dbi`
* `eirp_dbw`
* `fspl_db`
* `rain_db`
* `gas_db`
* `pointing_db`
* `rx_antenna_gain_dbi`
* `rx_system_temp_k` (or in dB/K format)
* `cn0_dbhz`
* `ebn0_db`
* `margin_db`

---

## 13. Payload Module Spec (Multi-Beam + Interference)

### 13.1 BeamSet

A BeamSet is a collection of beams defined by steering commands or weight vectors.

* Provide `Beam` objects:

  * `beam_id`
  * steering direction (az/el) or (theta/phi)
  * optional weight vectors (if advanced)
  * per-beam allocated power or constraints

### 13.2 BeamMap

Map users or angular points to a selected beam.
Outputs per grid point:

* serving beam ID
* signal C/N0, Eb/N0, throughput
* interference estimate from other beams (sidelobes)

### 13.3 Interference Model (v0.x pragmatic)

Provide a simple interference budget:

* treat each non-serving beam as an interferer with its gain toward victim direction
* sum interference powers in linear domain
* compute C/(N+I) equivalents

This avoids full network scheduling while enabling meaningful payload trade-offs.

---

## 14. World Model / Mission & Operational Simulation Spec (Time-Series)

### 14.1 Purpose

Convert snapshot evaluation into operational outcomes:

* margin(t), throughput(t)
* outage time, availability percent
* worst-case segments
* time-in-ModCod distribution (if ACM enabled)

### 14.2 Core Objects

```python
class TrajectoryProvider(Protocol):
    def states_ecef(self, t0_s: float, t1_s: float, dt_s: float) -> List[StateECEF]:
        ...

class EnvironmentProvider(Protocol):
    def conditions(self, t_s: float, terminal_a: Terminal, terminal_b: Terminal) -> PropagationConditions:
        ...

@dataclass(frozen=True)
class OpsPolicy:
    min_elevation_deg: float = 10.0
    max_scan_deg: float = 60.0
    handover_hysteresis_s: float = 5.0
    # Optional: ACM hold timers, etc.
```

### 14.3 World Simulation Engine

```python
@dataclass(frozen=True)
class WorldSimInputs:
    link_inputs: LinkInputs
    sat_traj: TrajectoryProvider
    ops: OpsPolicy
    env: EnvironmentProvider
    t0_s: float
    t1_s: float
    dt_s: float

@dataclass(frozen=True)
class WorldSimOutputs:
    times_s: np.ndarray
    elev_deg: np.ndarray
    range_m: np.ndarray
    margin_db: np.ndarray
    throughput_mbps: Optional[np.ndarray]
    selected_modcod: Optional[List[str]]
    outages_mask: np.ndarray
    summary: Dict[str, float]            # availability, outage_minutes, avg_thr, p05, p50, p95, worst_margin
    breakdown_timeseries: Optional[Dict[str, np.ndarray]]  # per-term losses over time
```

Rules:

* At each timestep:

  1. compute geometry: range/elev/az
  2. enforce ops policy:

     * if elev < min_elev → outage
     * if scan > max_scan → outage
  3. get propagation conditions from EnvironmentProvider
  4. evaluate snapshot link
  5. compute margin/throughput; mark outage if margin < 0 (or requirement not met)

### 14.4 Tiered World Model Scope

* Tier 1 (required): single satellite ↔ terminal time-series
* Tier 2 (optional): multi-sat handover heuristic:

  * evaluate candidate satellites
  * select best based on margin or throughput with hysteresis
* Tier 3 (deferred): network traffic + scheduling

---

## 15. Trades Module Spec (PAS Integration)

### 15.1 Standard Metric Output Schema

For DOE and batch runs, output rows with:

* independent variables (inputs)
* derived metrics (margin, throughput, cost proxy, power)
* constraints (pass/fail booleans)
* metadata (case_id, seed, run_id, timestamps)

### 15.2 Requirements Templates (SatCom)

Provide helpers:

* `MinLinkMargin(metric="margin_db_p05", threshold=3.0)`
* `MinAvailability(threshold=0.999)`
* `MinThroughput(metric="throughput_mbps_p50", threshold=50.0)`
* `MaxDCpower(threshold=...)`
* `MaxMass(threshold=...)`

### 15.3 DOE Generation Helpers

Expose a simple wrapper around PAS patterns:

* `opensatcom.doe(config, n=200, method="lhs")`
* `opensatcom.run_batch(cases, parallel=True)`

---

## 16. Reports Module Spec

### 16.1 Report Types

1. **Snapshot link report**

   * link breakdown table
   * margin vs elevation plot
   * pattern cut plots if requested
2. **Mission/time-series report**

   * margin(t), throughput(t)
   * outage segments highlighted
   * histograms: throughput distribution, time-in-ModCod
   * summary metrics
3. **Trade study report**

   * Pareto plots
   * constraint satisfaction rates
   * sensitivity plots (variable importance, partial dependence if desired)

### 16.2 Artifact Folder Layout

```
run_<timestamp>_<id>/
  config_snapshot.yaml
  results.parquet
  link_breakdown.csv
  plots/
    margin_vs_time.png
    throughput_vs_time.png
    margin_hist.png
  patterns/              # optional
  beam_maps/             # optional
  report.html
```

---

## 17. CLI Spec

Provide a single top-level CLI: `opensatcom`

### 17.1 Commands

* `opensatcom run config.yaml`
* `opensatcom mission config.yaml` (time-series)
* `opensatcom doe config.yaml -n 500 --method lhs`
* `opensatcom batch cases.parquet --parallel`
* `opensatcom report results.parquet --format html`
* `opensatcom pareto results.parquet --x cost_usd --y throughput_p50`

### 17.2 Exit Codes

* 0 success
* 2 invalid config
* 3 runtime evaluation failure
* 4 missing optional dependency (with actionable message)

---

## 18. Config Schema (YAML) — Comprehensive

### 18.1 High-Level Example

```yaml
project:
  name: "leo_user_terminal"
  seed: 42
  output_dir: "./runs"

scenario:
  name: "downlink_ku_demo"
  direction: "downlink"
  freq_hz: 19.7e9
  bandwidth_hz: 200e6
  polarization: "RHCP"
  required_metric: "ebn0_db"
  required_value: 6.0

terminals:
  tx:
    name: "sat_payload"
    lat_deg: 0.0
    lon_deg: 0.0
    alt_m: 550000.0
  rx:
    name: "user_terminal"
    lat_deg: 47.6062
    lon_deg: -122.3321
    alt_m: 50.0
    system_noise_temp_k: 500.0

antenna:
  tx:
    model: "pam"
    pam:
      nx: 16
      ny: 16
      dx_lambda: 0.5
      dy_lambda: 0.5
      taper: { type: "taylor", sidelobe_db: -28 }
      steering: { type: "azel", az_deg: 0.0, el_deg: 45.0 }
      impairments:
        phase_bits: 5
        amp_bits: 6
        failed_elements_pct: 1.0
        element_position_jitter_m: 0.0005
    coupling:
      enabled: false
      source: "edgefem"
      artifact_path: "./edgefem_runs/unitcell_kband.npz"
  rx:
    model: "parametric"
    parametric:
      gain_dbi: 35.0
      scan_loss_model: "none"

rf_chain:
  tx_power_w: 200.0
  tx_losses_db: 2.0
  rx_noise_temp_k: 500.0

propagation:
  model: "composite"
  components:
    - type: "fspl"
    - type: "itur_rain"     # optional adapter
      availability_target: 0.999
      climate_region: "seattle_wa"
    - type: "itur_gas"      # optional adapter

modem:
  enabled: true
  target_bler: 1.0e-5
  modcod_table: "./modcods/dvbs2x_example.json"
  curves:
    type: "required_ebn0_table"
    path: "./modcods/dvbs2x_required_ebn0.csv"
  acm_policy:
    type: "hysteresis"
    hysteresis_db: 0.5
    hold_time_s: 2.0

world:
  enabled: true
  t0_s: 0
  t1_s: 1200
  dt_s: 1.0
  trajectory:
    type: "plugin"
    plugin_name: "sgp4_adapter"
    tle_path: "./tles/demo.tle"
  ops_policy:
    min_elevation_deg: 10
    max_scan_deg: 60

trades:
  enabled: true
  method: "lhs"
  n_cases: 200
  variables:
    - path: "antenna.tx.pam.nx"
      type: "int"
      low: 8
      high: 32
    - path: "rf_chain.tx_power_w"
      type: "float"
      low: 50
      high: 500
  objectives:
    - metric: "cost_usd"
      sense: "minimize"
    - metric: "throughput_mbps_p50"
      sense: "maximize"
  requirements:
    - metric: "availability"
      op: ">="
      value: 0.999
    - metric: "margin_db_p05"
      op: ">="
      value: 3.0

reports:
  format: "html"
  include_plots: true
```

---

## 19. Validation & Testing Spec

### 19.1 Golden Test Vectors

Provide a `tests/golden/` suite:

* Snapshot link budgets (FSPL only)
* Snapshot + rain loss (if adapter available)
* Mission pass simulation with known geometry inputs (pre-baked time series)
* ModCod selection logic and hysteresis behavior

Golden outputs:

* expected `cn0_dbhz`, `ebn0_db`, `margin_db` within tolerance
* expected availability and outage minutes
* expected chosen ModCod sequence for a known Eb/N0(t)

### 19.2 Regression Testing

* Freeze representative configs in `examples/` and re-run in CI
* Any metric drift requires explicit “baseline update” PR

### 19.3 Numerical Stability

* Avoid subtractive cancellation in dB conversions
* Sum noise/interference in linear domain then convert to dB

---

## 20. Performance Requirements

### 20.1 Snapshot Evaluation

* Must support vectorized evaluation over many elevations/time steps
* Must not require recomputing patterns unnecessarily:

  * cache pattern grids by (f_hz, steering, impairments) keys

### 20.2 Batch/DOE

* Parallel evaluation:

  * multiprocess for CPU-bound tasks
  * progress logging
* Output should be parquet for speed and interoperability

---

## 21. Documentation Spec

### 21.1 Docs Structure

* `docs/quickstart.md`
* `docs/tutorials/`

  * snapshot link closure
  * mission simulation
  * trade study
  * coupling-aware ingestion
* `docs/theory/`

  * link budget equations and term definitions
  * ModCod/ACM modeling assumptions
  * propagation model assumptions
* `docs/api/` (autogenerated)

### 21.2 Example Notebooks

* `examples/01_snapshot_link.ipynb`
* `examples/02_mission_pass.ipynb`
* `examples/03_trade_study.ipynb`
* `examples/04_multibeam_capacity.ipynb`

---

## 22. Roadmap (P0/P1/P2)

### P0 (v0.1): Core Link + Mission + ModCod Abstraction

* Snapshot link engine with breakdown outputs
* Composite propagation with FSPL built-in; plugin hooks for atmospheric/rain
* ModCod tables + performance curve loading + ACM hysteresis policy
* WorldSim Tier 1: time-series pass simulation using provided az/el/range time series or a simple trajectory plugin
* HTML report generation for snapshot + mission runs
* Golden tests for FSPL + mission + ACM

### P1 (v0.2): Multi-Beam Payload + Interference

* BeamSet + BeamMap
* simple interference model and capacity maps
* report support for beam maps

### P2 (v0.3+): Coupling-Aware Fidelity + Tier 2 Ops

* EdgeFEM coupling ingestion end-to-end
* Handover heuristic among multiple satellites (Tier 2)
* richer RF chain and interference/linearity modeling hooks

---

## 23. Implementation Notes (Key Design Choices)

1. **Keep OpenSatCom a domain layer**: do not fork PAM/PAS; wrap them.
2. **World model is “thin”**: time series + policies, not a full network sim.
3. **ModCod is abstraction-first**: tables/curves, no bit-level LDPC sim.
4. **Everything produces artifacts**: results + plots + config snapshot by default.
5. **Plugin seams**: orbit/propagation/curves should be swappable.

---

## 24. Minimal “Hello World” Public Example

```python
from opensatcom.core import Terminal, Scenario, PropagationConditions
from opensatcom.antenna import PamArrayAntenna, ParametricAntenna
from opensatcom.propagation import FreeSpacePropagation, CompositePropagation
from opensatcom.link import DefaultLinkEngine, LinkInputs
from opensatcom.rf import RFChainModel

tx = Terminal("sat", 0, 0, 550e3)
rx = Terminal("ut", 47.6062, -122.3321, 50, system_noise_temp_k=500)

sc = Scenario("dl", "downlink", 19.7e9, 200e6, "RHCP", "ebn0_db", 6.0)

tx_ant = PamArrayAntenna(nx=16, ny=16, dx_lambda=0.5, dy_lambda=0.5, taper=("taylor",-28))
rx_ant = ParametricAntenna(gain_dbi=35)

prop = CompositePropagation([FreeSpacePropagation()])
rf = RFChainModel(tx_power_w=200, tx_losses_db=2.0, rx_noise_temp_k=500)

inputs = LinkInputs(tx, rx, sc, tx_ant, rx_ant, prop, rf)

engine = DefaultLinkEngine()
out = engine.evaluate_snapshot(elev_deg=30, az_deg=0, range_m=1200e3,
                               inputs=inputs, cond=PropagationConditions())

print(out.margin_db, out.ebn0_db, out.cn0_dbhz)
```

---

## 25. Deliverables Checklist (what “done” looks like for v0.1)

* [ ] `opensatcom` package skeleton with modules and stable interfaces
* [ ] Snapshot link engine with breakdown table
* [ ] ModCod table loader + required Eb/N0 curve + ACM hysteresis policy
* [ ] WorldSim Tier 1 with time-series outputs + summary metrics
* [ ] CLI: run / mission / report
* [ ] Reports: HTML snapshot + mission
* [ ] Parquet results + artifact folder outputs
* [ ] Golden tests + CI pipeline + docs quickstart

---

# Appendix A: Core Metrics (definitions)

* **EIRP (dBW)**: Effective isotropic radiated power in direction of interest.
* **G/T (dB/K)**: Receiver figure of merit.
* **C/N₀ (dB-Hz)**: Carrier power to noise spectral density.
* **Eb/N₀ (dB)**: Energy per bit to noise spectral density.
* **Margin (dB)**: Achieved metric − required metric (e.g., Eb/N0 margin).
* **Availability**: fraction of time meeting requirements under ops policy and conditions.
* **Throughput (Mbps)**: net payload rate from ModCod + overhead assumptions.

# Appendix B: Common Extensions

* Add Doppler to modem impairment models (optional)
* Add polarization mismatch modeling if you have basis vectors
* Add PFD/EIRP density outputs for regulatory-style metrics

```

If you want this spec to match *your repos’ exact style* (naming, config patterns, CLI conventions), paste one example config/CLI usage from `phased-array-systems` and I’ll refit the spec to mirror it line-for-line.
::contentReference[oaicite:0]{index=0}
```
