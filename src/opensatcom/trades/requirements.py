"""Requirements templates for trade study parameter sweeps."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RequirementsTemplate:
    """Defines parameter sweep ranges for DOE/trade studies.

    Parameters are stored as (name, min, max) tuples describing the
    design space to explore.

    Example
    -------
    >>> rt = RequirementsTemplate()
    >>> rt.add("freq_hz", 10e9, 30e9)
    >>> rt.add("tx_power_w", 10.0, 200.0)
    >>> space = rt.to_parameter_space()
    """

    parameters: dict[str, tuple[float, float]] = field(default_factory=dict)

    def add(self, name: str, lo: float, hi: float) -> None:
        """Add a parameter with its range."""
        if lo > hi:
            raise ValueError(f"lo ({lo}) must be <= hi ({hi}) for parameter '{name}'")
        self.parameters[name] = (lo, hi)

    def to_parameter_space(self) -> dict[str, tuple[float, float]]:
        """Return the parameter space as a dict of (min, max) tuples."""
        return dict(self.parameters)

    @property
    def names(self) -> list[str]:
        return list(self.parameters.keys())

    @property
    def n_params(self) -> int:
        return len(self.parameters)
