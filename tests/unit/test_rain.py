"""Tests for ITU-R P.618 rain attenuation model."""


from opensatcom.core.models import PropagationConditions
from opensatcom.propagation.rain import RainAttenuationP618


class TestRainAttenuationP618:
    def test_zero_rain_rate(self) -> None:
        model = RainAttenuationP618(rain_rate_mm_per_hr=0.0)
        loss = model.total_path_loss_db(12e9, 30.0, 1e6, PropagationConditions())
        assert loss == 0.0

    def test_no_rain_rate(self) -> None:
        model = RainAttenuationP618()
        loss = model.total_path_loss_db(12e9, 30.0, 1e6, PropagationConditions())
        assert loss == 0.0

    def test_rain_from_conditions(self) -> None:
        model = RainAttenuationP618()
        cond = PropagationConditions(rain_rate_mm_per_hr=25.0)
        loss = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        assert loss > 0.0

    def test_loss_increases_with_frequency(self) -> None:
        model = RainAttenuationP618(rain_rate_mm_per_hr=25.0)
        cond = PropagationConditions()
        loss_12 = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        loss_20 = model.total_path_loss_db(20e9, 30.0, 1e6, cond)
        loss_30 = model.total_path_loss_db(30e9, 30.0, 1e6, cond)
        assert loss_20 > loss_12
        assert loss_30 > loss_20

    def test_loss_decreases_with_elevation(self) -> None:
        model = RainAttenuationP618(rain_rate_mm_per_hr=25.0)
        cond = PropagationConditions()
        loss_10 = model.total_path_loss_db(12e9, 10.0, 1e6, cond)
        loss_30 = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        loss_60 = model.total_path_loss_db(12e9, 60.0, 1e6, cond)
        assert loss_10 > loss_30
        assert loss_30 > loss_60

    def test_zero_at_low_frequency(self) -> None:
        model = RainAttenuationP618(rain_rate_mm_per_hr=25.0)
        cond = PropagationConditions()
        loss = model.total_path_loss_db(0.5e9, 30.0, 1e6, cond)
        assert loss == 0.0

    def test_loss_positive_at_ku_band(self) -> None:
        model = RainAttenuationP618(rain_rate_mm_per_hr=25.0)
        cond = PropagationConditions()
        loss = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        assert loss > 0.5  # Should be meaningful at Ku-band

    def test_conforms_to_protocol(self) -> None:
        from opensatcom.core.protocols import PropagationModel

        model = RainAttenuationP618()
        assert isinstance(model, PropagationModel)
