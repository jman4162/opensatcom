# Tutorial Notebooks

Interactive Jupyter notebooks covering all major OpenSatCom workflows. Each notebook runs in Google Colab with zero local setup.

| Notebook | Topic | Colab |
|----------|-------|-------|
| `01_quickstart.ipynb` | End-to-end snapshot link budget | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/01_quickstart.ipynb) |
| `02_mission_simulation.ipynb` | Time-series mission simulation | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/02_mission_simulation.ipynb) |
| `03_multibeam_payload.ipynb` | Multi-beam capacity analysis | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/03_multibeam_payload.ipynb) |
| `04_propagation_models.ipynb` | Propagation model comparison | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/04_propagation_models.ipynb) |
| `05_trade_studies.ipynb` | DOE + Pareto workflow | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/opensatcom/blob/main/notebooks/05_trade_studies.ipynb) |

## Running Locally

```bash
pip install opensatcom[notebooks]
jupyter lab notebooks/
```
