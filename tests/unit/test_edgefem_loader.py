"""Tests for EdgeFEM artifact loading."""

from pathlib import Path

import numpy as np
import pytest

from opensatcom.antenna.edgefem_loader import (
    CouplingData,
    load_npz_artifact,
    load_touchstone_coupling,
)

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "synthetic_coupling.npz"


class TestLoadNpzArtifact:
    def test_load_synthetic(self) -> None:
        data = load_npz_artifact(FIXTURE_PATH)
        assert isinstance(data, CouplingData)
        assert data.n_elements == 4
        assert data.coupling_matrix.shape == (4, 4)
        assert data.element_patterns.shape[0] == 4
        assert len(data.theta_grid_deg) > 0
        assert len(data.phi_grid_deg) > 0

    def test_element_patterns_shape(self) -> None:
        data = load_npz_artifact(FIXTURE_PATH)
        n_theta = len(data.theta_grid_deg)
        n_phi = len(data.phi_grid_deg)
        assert data.element_patterns.shape == (4, n_theta, n_phi)

    def test_coupling_matrix_is_complex(self) -> None:
        data = load_npz_artifact(FIXTURE_PATH)
        assert np.iscomplexobj(data.coupling_matrix)

    def test_array_positions(self) -> None:
        data = load_npz_artifact(FIXTURE_PATH)
        assert data.array_positions_m.shape == (4, 2)

    def test_freq_scalar(self) -> None:
        data = load_npz_artifact(FIXTURE_PATH)
        assert isinstance(data.freq_hz, float)
        assert data.freq_hz == pytest.approx(10e9)

    def test_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_npz_artifact("/nonexistent/path.npz")

    def test_missing_array(self, tmp_path: Path) -> None:
        # Create .npz missing required fields
        path = tmp_path / "bad.npz"
        np.savez(path, coupling_matrix=np.eye(2))
        with pytest.raises(ValueError, match="Missing required"):
            load_npz_artifact(path)


class TestLoadTouchstoneCoupling:
    def test_parse_s2p_ma_format(self, tmp_path: Path) -> None:
        """Parse a minimal 2-port Touchstone file in MA format."""
        content = """! 2-port S-parameters
# GHz S MA R 50
10.0  0.1 45.0  0.8 -10.0  0.8 -10.0  0.1 45.0
"""
        path = tmp_path / "test.s2p"
        path.write_text(content)
        s_matrix = load_touchstone_coupling(path)
        assert s_matrix.shape == (2, 2)
        assert np.iscomplexobj(s_matrix)
        # S11 should be 0.1 at 45 degrees
        assert abs(s_matrix[0, 0]) == pytest.approx(0.1, abs=0.001)

    def test_parse_s2p_ri_format(self, tmp_path: Path) -> None:
        """Parse a 2-port Touchstone file in RI format."""
        content = """# GHz S RI R 50
10.0  0.05 0.05  0.7 -0.1  0.7 -0.1  0.05 0.05
"""
        path = tmp_path / "test.s2p"
        path.write_text(content)
        s_matrix = load_touchstone_coupling(path)
        assert s_matrix.shape == (2, 2)
        assert s_matrix[0, 0] == pytest.approx(complex(0.05, 0.05), abs=0.001)

    def test_missing_touchstone_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_touchstone_coupling("/nonexistent.s2p")

    def test_invalid_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "test.txt"
        path.write_text("data")
        with pytest.raises(ValueError, match="Not a Touchstone"):
            load_touchstone_coupling(path)
