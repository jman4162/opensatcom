"""Tests for tropospheric scintillation fade model."""


from opensatcom.core.models import PropagationConditions
from opensatcom.propagation.scintillation import ScintillationLoss


class TestScintillationLoss:
    def test_increases_at_low_elevation(self) -> None:
        model = ScintillationLoss(availability_target=0.99)
        cond = PropagationConditions()
        loss_10 = model.total_path_loss_db(12e9, 10.0, 1e6, cond)
        loss_30 = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        loss_60 = model.total_path_loss_db(12e9, 60.0, 1e6, cond)
        assert loss_10 > loss_30
        assert loss_30 > loss_60

    def test_small_at_high_elevation(self) -> None:
        """Near zenith, scintillation should be minimal."""
        model = ScintillationLoss(availability_target=0.99)
        cond = PropagationConditions()
        loss = model.total_path_loss_db(12e9, 89.0, 1e6, cond)
        assert loss < 0.5  # Small near zenith

    def test_increases_with_frequency(self) -> None:
        model = ScintillationLoss(availability_target=0.99)
        cond = PropagationConditions()
        loss_4 = model.total_path_loss_db(4e9, 30.0, 1e6, cond)
        loss_12 = model.total_path_loss_db(12e9, 30.0, 1e6, cond)
        loss_30 = model.total_path_loss_db(30e9, 30.0, 1e6, cond)
        assert loss_12 > loss_4
        assert loss_30 > loss_12

    def test_zero_below_1ghz(self) -> None:
        model = ScintillationLoss()
        cond = PropagationConditions()
        loss = model.total_path_loss_db(0.5e9, 30.0, 1e6, cond)
        assert loss == 0.0

    def test_higher_availability_more_margin(self) -> None:
        model_99 = ScintillationLoss(availability_target=0.99)
        model_999 = ScintillationLoss(availability_target=0.999)
        cond = PropagationConditions()
        loss_99 = model_99.total_path_loss_db(12e9, 30.0, 1e6, cond)
        loss_999 = model_999.total_path_loss_db(12e9, 30.0, 1e6, cond)
        assert loss_999 > loss_99

    def test_conforms_to_protocol(self) -> None:
        from opensatcom.core.protocols import PropagationModel

        model = ScintillationLoss()
        assert isinstance(model, PropagationModel)
