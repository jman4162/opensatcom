"""Core datamodels, units, constants, and protocols for OpenSatCom."""

from opensatcom.core.constants import (
    BOLTZMANN_DBW_PER_K_HZ,
    EARTH_RADIUS_M,
    SPEED_OF_LIGHT_MPS,
)
from opensatcom.core.models import (
    LinkInputs,
    LinkOutputs,
    ModCod,
    OpsPolicy,
    PropagationConditions,
    RFChainModel,
    Scenario,
    StateECEF,
    Terminal,
    WorldSimInputs,
    WorldSimOutputs,
)
from opensatcom.core.protocols import (
    ACMPolicy,
    AntennaModel,
    EnvironmentProvider,
    LinkEngine,
    PerformanceCurve,
    PropagationModel,
    TrajectoryProvider,
)
from opensatcom.core.units import (
    db10_to_lin,
    db20_to_lin,
    dbw_to_w,
    lin_to_db10,
    lin_to_db20,
    w_to_dbw,
)

__all__ = [
    "BOLTZMANN_DBW_PER_K_HZ",
    "EARTH_RADIUS_M",
    "SPEED_OF_LIGHT_MPS",
    "LinkInputs",
    "LinkOutputs",
    "ModCod",
    "OpsPolicy",
    "PropagationConditions",
    "RFChainModel",
    "Scenario",
    "StateECEF",
    "Terminal",
    "WorldSimInputs",
    "WorldSimOutputs",
    "ACMPolicy",
    "AntennaModel",
    "EnvironmentProvider",
    "LinkEngine",
    "PerformanceCurve",
    "PropagationModel",
    "TrajectoryProvider",
    "db10_to_lin",
    "db20_to_lin",
    "dbw_to_w",
    "lin_to_db10",
    "lin_to_db20",
    "w_to_dbw",
]
