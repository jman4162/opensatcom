"""Tests for ITU-R P.676 gaseous absorption model."""


from opensatcom.core.models import PropagationConditions
from opensatcom.propagation.gas import GaseousAbsorptionP676


class TestGaseousAbsorptionP676:
    def test_positive_loss_at_20ghz(self) -> None:
        model = GaseousAbsorptionP676()
        cond = PropagationConditions()
        loss = model.total_path_loss_db(20e9, 45.0, 1e6, cond)
        assert loss > 0.0

    def test_high_loss_at_60ghz(self) -> None:
        """O2 resonance near 60 GHz should produce large absorption."""
        model = GaseousAbsorptionP676()
        cond = PropagationConditions()
        loss_60 = model.total_path_loss_db(60e9, 45.0, 1e6, cond)
        loss_20 = model.total_path_loss_db(20e9, 45.0, 1e6, cond)
        assert loss_60 > loss_20 * 5  # Much larger at O2 resonance

    def test_monotonic_with_path_length(self) -> None:
        """Lower elevation = longer path = more loss."""
        model = GaseousAbsorptionP676()
        cond = PropagationConditions()
        loss_10 = model.total_path_loss_db(20e9, 10.0, 1e6, cond)
        loss_45 = model.total_path_loss_db(20e9, 45.0, 1e6, cond)
        loss_90 = model.total_path_loss_db(20e9, 90.0, 1e6, cond)
        assert loss_10 > loss_45
        assert loss_45 > loss_90

    def test_zero_below_1ghz(self) -> None:
        model = GaseousAbsorptionP676()
        cond = PropagationConditions()
        loss = model.total_path_loss_db(0.5e9, 30.0, 1e6, cond)
        assert loss == 0.0

    def test_water_vapor_effect(self) -> None:
        """Higher water vapor density should increase loss."""
        model_dry = GaseousAbsorptionP676(water_vapor_density_g_m3=1.0)
        model_wet = GaseousAbsorptionP676(water_vapor_density_g_m3=15.0)
        cond = PropagationConditions()
        loss_dry = model_dry.total_path_loss_db(22e9, 30.0, 1e6, cond)
        loss_wet = model_wet.total_path_loss_db(22e9, 30.0, 1e6, cond)
        assert loss_wet > loss_dry

    def test_conforms_to_protocol(self) -> None:
        from opensatcom.core.protocols import PropagationModel

        model = GaseousAbsorptionP676()
        assert isinstance(model, PropagationModel)
