# CLI Reference

OpenSatCom provides a command-line interface for all major workflows. All commands are invoked via `opensatcom <command>`.

```bash
opensatcom --version      # Print version
opensatcom --help         # Show available commands
```

---

## `opensatcom run`

Evaluate a snapshot link budget from a YAML config file.

```bash
opensatcom run config.yaml
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `config` | Path to YAML config file |

**Outputs:** `config_snapshot.yaml`, `results.parquet`, `report.html`, link breakdown CSV.

**Example output:**

```
Snapshot link budget complete. Margin: 12.34 dB
  EIRP:       56.00 dBW
  Path loss:  205.23 dB
  C/N0:       78.45 dB-Hz
  Eb/N0:      12.90 dB
  Margin:     12.34 dB
Artifacts saved to: runs/my-project/
```

---

## `opensatcom mission`

Run a time-series mission simulation (Tier 1 single-sat pass).

```bash
opensatcom mission config.yaml
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `config` | Path to YAML config file (must include `world` section) |

**Outputs:** `config_snapshot.yaml`, `results.parquet` (time-series), `report.html` with interactive plots.

---

## `opensatcom beammap`

Evaluate a multi-beam capacity map across an angular grid.

```bash
opensatcom beammap config.yaml
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `config` | Path to YAML config file (must include `payload` section) |

**Outputs:** `config_snapshot.yaml`, `beammap.parquet`, `report.html` with SINR heatmaps.

---

## `opensatcom doe`

Generate design-of-experiments parameter cases for trade studies.

```bash
opensatcom doe config.yaml -n 500 --method lhs
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `config` | Path to YAML config file (must include `trades.parameters` section) |
| `-n` | Number of cases to generate (default: 200) |
| `--method` | Sampling method: `lhs`, `random`, or `factorial` (default: `lhs`) |

**Outputs:** `cases.parquet` with one row per parameter combination.

---

## `opensatcom batch`

Batch-evaluate parameter cases from a parquet file.

```bash
opensatcom batch cases.parquet --parallel
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `cases` | Path to cases parquet file (from `doe` command) |
| `--parallel` | Enable parallel execution using multiprocessing |

**Outputs:** `results.parquet` with evaluation metrics for each case.

---

## `opensatcom pareto`

Extract the Pareto-optimal front from batch results.

```bash
opensatcom pareto results.parquet --x cost_usd --y throughput_p50
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `results` | Path to results parquet file (from `batch` command) |
| `--x` | X-axis metric column name (required) |
| `--y` | Y-axis metric column name (required) |

**Outputs:** `pareto.parquet` (optimal points) and `pareto.png` (scatter plot).

---

## `opensatcom report`

Generate an HTML report from existing results.

```bash
opensatcom report results.parquet --format html
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `results` | Path to results parquet file |
| `--format` | Output format: `html` or `pdf` (default: `html`) |

Auto-detects result type (snapshot vs. mission) based on columns present.

---

## Typical Workflow

```bash
# 1. Quick snapshot evaluation
opensatcom run my_link.yaml

# 2. Full mission simulation
opensatcom mission my_link.yaml

# 3. Trade study pipeline
opensatcom doe my_link.yaml -n 500 --method lhs
opensatcom batch cases.parquet --parallel
opensatcom pareto results.parquet --x cost_usd --y margin_db
opensatcom report results.parquet
```
