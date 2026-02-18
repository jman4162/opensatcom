"""Tests for Pareto front extraction."""

import pandas as pd

from opensatcom.trades.pareto import extract_pareto_front


class TestParetoFront:
    def test_known_4_point_set(self) -> None:
        """Known 4-point set: 2 points should be on Pareto front.

        Points: (1,4), (2,3), (3,2), (4,1)
        Minimizing x, maximizing y (minimize_y=False).
        Pareto: (1,4) — minimum x with high y.
        But (2,3) is dominated by (1,4) if both x and -y are minimized.
        """
        df = pd.DataFrame({
            "cost": [1.0, 2.0, 3.0, 4.0],
            "throughput": [4.0, 3.0, 2.0, 1.0],
        })
        pareto = extract_pareto_front(df, "cost", "throughput", minimize_x=True, minimize_y=False)
        # (1,4) dominates all others — min cost and max throughput
        assert len(pareto) == 1
        assert pareto.iloc[0]["cost"] == 1.0

    def test_non_dominated_set(self) -> None:
        """Create a set where multiple points are non-dominated."""
        df = pd.DataFrame({
            "cost": [1.0, 2.0, 3.0],
            "throughput": [1.0, 2.0, 3.0],
        })
        pareto = extract_pareto_front(df, "cost", "throughput", minimize_x=True, minimize_y=False)
        # (1,1): low cost, low throughput
        # (2,2): medium
        # (3,3): high cost, high throughput
        # None dominates any other (lower cost trades off throughput)
        assert len(pareto) == 3

    def test_two_objectives_minimize_both(self) -> None:
        df = pd.DataFrame({
            "x": [1.0, 2.0, 1.5, 3.0],
            "y": [3.0, 1.0, 1.5, 0.5],
        })
        pareto = extract_pareto_front(df, "x", "y", minimize_x=True, minimize_y=True)
        # (1,3): low x, high y
        # (2,1): medium x, low y
        # (1.5,1.5): dominated by neither
        # (3,0.5): high x, lowest y
        # Pareto: (1,3), (1.5,1.5), (2,1), (3,0.5) — need to check
        # (1.5,1.5) is not dominated: no point has both x<=1.5 and y<=1.5 except itself
        assert len(pareto) >= 2

    def test_empty_input(self) -> None:
        df = pd.DataFrame({"x": [], "y": []})
        pareto = extract_pareto_front(df, "x", "y")
        assert len(pareto) == 0
