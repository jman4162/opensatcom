"""EdgeFEM artifact loading — coupling matrices and element patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class CouplingData:
    """Parsed coupling and element pattern data from EdgeFEM artifacts.

    Attributes
    ----------
    coupling_matrix : complex S-parameter matrix, shape (N_elem, N_elem)
    element_patterns : complex gain per element, shape (N_elem, N_theta, N_phi)
    theta_grid_deg : elevation angle grid, shape (N_theta,)
    phi_grid_deg : azimuth angle grid, shape (N_phi,)
    freq_hz : frequency (scalar or array of frequencies)
    array_positions_m : element positions, shape (N_elem, 2) or (N_elem, 3)
    metadata : additional metadata from the artifact
    """

    coupling_matrix: np.ndarray
    element_patterns: np.ndarray
    theta_grid_deg: np.ndarray
    phi_grid_deg: np.ndarray
    freq_hz: float | np.ndarray
    array_positions_m: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def n_elements(self) -> int:
        return self.coupling_matrix.shape[0]


def load_npz_artifact(path: str | Path) -> CouplingData:
    """Load an EdgeFEM artifact from a .npz file.

    Expected arrays in the .npz:
    - coupling_matrix: (N_elem, N_elem) complex
    - element_patterns: (N_elem, N_theta, N_phi) complex
    - theta_grid_deg: (N_theta,)
    - phi_grid_deg: (N_phi,)
    - freq_hz: scalar or (N_freq,)
    - array_positions_m: (N_elem, 2) or (N_elem, 3)

    Optional:
    - metadata_keys, metadata_values: parallel arrays for metadata
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"EdgeFEM artifact not found: {path}")

    data = np.load(path, allow_pickle=True)

    required = ["coupling_matrix", "element_patterns", "theta_grid_deg",
                 "phi_grid_deg", "freq_hz", "array_positions_m"]
    for key in required:
        if key not in data:
            raise ValueError(f"Missing required array '{key}' in {path}")

    freq = data["freq_hz"]
    freq_val: float | np.ndarray = float(freq) if freq.ndim == 0 else freq

    metadata: dict[str, Any] = {}
    if "metadata_keys" in data and "metadata_values" in data:
        keys = data["metadata_keys"]
        vals = data["metadata_values"]
        for k, v in zip(keys, vals):
            metadata[str(k)] = v

    return CouplingData(
        coupling_matrix=data["coupling_matrix"],
        element_patterns=data["element_patterns"],
        theta_grid_deg=data["theta_grid_deg"],
        phi_grid_deg=data["phi_grid_deg"],
        freq_hz=freq_val,
        array_positions_m=data["array_positions_m"],
        metadata=metadata,
    )


def load_touchstone_coupling(
    s_param_path: str | Path,
    pattern_path: str | Path | None = None,
) -> np.ndarray:
    """Load S-parameter coupling matrix from a Touchstone .sNp file.

    Returns the coupling matrix at the first frequency point.
    Only the S-parameter matrix is extracted; element patterns must be
    provided separately (e.g., via .npz).

    Parameters
    ----------
    s_param_path : path to .sNp Touchstone file
    pattern_path : unused, reserved for future pattern file loading
    """
    path = Path(s_param_path)
    if not path.exists():
        raise FileNotFoundError(f"Touchstone file not found: {path}")

    # Determine number of ports from extension
    suffix = path.suffix.lower()
    if not suffix.startswith(".s") or not suffix.endswith("p"):
        raise ValueError(f"Not a Touchstone file: {path}")
    n_ports = int(suffix[2:-1])

    freq_list: list[float] = []
    s_data_rows: list[list[float]] = []
    data_format = "ma"  # default: magnitude/angle

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            if line.startswith("#"):
                # Option line: # GHz S MA R 50
                parts = line[1:].split()
                for p in parts:
                    if p.upper() in ("MA", "DB", "RI"):
                        data_format = p.upper()
                continue

            # Data line
            values = [float(x) for x in line.split()]
            if len(values) > 2 * n_ports * n_ports:
                # Frequency + S-data on one line
                freq_list.append(values[0])
                s_data_rows.append(values[1:])
            elif freq_list and len(s_data_rows[-1]) < 2 * n_ports * n_ports:
                # Continuation line
                s_data_rows[-1].extend(values)
            else:
                freq_list.append(values[0])
                s_data_rows.append(values[1:])

    if not freq_list:
        raise ValueError(f"No data found in Touchstone file: {path}")

    # Parse first frequency point into complex S-matrix
    row = s_data_rows[0]
    s_matrix = np.zeros((n_ports, n_ports), dtype=complex)

    for i in range(n_ports):
        for j in range(n_ports):
            idx = (i * n_ports + j) * 2
            if idx + 1 >= len(row):
                break
            v1, v2 = row[idx], row[idx + 1]
            if data_format == "MA":
                s_matrix[i, j] = v1 * np.exp(1j * np.radians(v2))
            elif data_format == "DB":
                mag = 10 ** (v1 / 20.0)
                s_matrix[i, j] = mag * np.exp(1j * np.radians(v2))
            elif data_format == "RI":
                s_matrix[i, j] = complex(v1, v2)

    return s_matrix
