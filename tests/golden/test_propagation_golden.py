"""Golden test vectors for propagation models."""

import pytest

from opensatcom.core.models import PropagationConditions
from opensatcom.propagation.gas import GaseousAbsorptionP676
from opensatcom.propagation.rain import RainAttenuationP618
from opensatcom.propagation.scintillation import ScintillationLoss


@pytest.mark.golden
class TestPropagationGolden:
    def test_rain_12ghz_30deg_25mm(self) -> None:
        """Frozen: rain loss at 12 GHz, 30 deg elev, 25 mm/hr."""
        model = RainAttenuationP618(rain_rate_mm_per_hr=25.0, availability_target=0.99)
        cond = PropagationConditions()
        loss = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        assert loss == pytest.approx(0.6081, abs=0.01)

    def test_gas_20ghz_45deg(self) -> None:
        """Frozen: gaseous absorption at 20 GHz, 45 deg elevation."""
        model = GaseousAbsorptionP676(water_vapor_density_g_m3=7.5)
        cond = PropagationConditions()
        loss = model.total_path_loss_db(20e9, 45.0, 1e6, cond)
        assert loss == pytest.approx(0.2509, abs=0.01)

    def test_scintillation_12ghz_30deg(self) -> None:
        """Frozen: scintillation at 12 GHz, 30 deg, 99% availability."""
        model = ScintillationLoss(availability_target=0.99)
        cond = PropagationConditions()
        loss = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        assert loss == pytest.approx(0.8200, abs=0.01)
