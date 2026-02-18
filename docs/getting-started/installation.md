# Installation

## Requirements

- Python 3.10 or later

## Install from PyPI

```bash
pip install opensatcom
```

## Optional Extras

```bash
# Development tools (pytest, mypy, ruff, coverage)
pip install opensatcom[dev]

# Jupyter notebooks
pip install opensatcom[notebooks]

# ITU-R propagation models (requires itur package)
pip install opensatcom[itur]

# Orbit propagation (SGP4 + Skyfield)
pip install opensatcom[orbit]

# Documentation building
pip install opensatcom[docs]
```

## Install from Source

```bash
git clone https://github.com/jman4162/opensatcom.git
cd opensatcom
pip install -e ".[dev]"
```

## Verify Installation

```python
import opensatcom
from opensatcom.core.models import Terminal, Scenario
print("OpenSatCom installed successfully!")
```

## Core Dependencies

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations |
| `pandas` | DataFrames and I/O |
| `pyyaml` | YAML config loading |
| `pydantic` | Config validation |
| `matplotlib` | Base plotting |
| `pyarrow` | Parquet I/O |
| `scipy` | LHS sampling, interpolation |
| `plotly` | Interactive visualizations |
| `seaborn` | Statistical plots |
