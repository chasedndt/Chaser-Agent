"""The offline calibration tool: numerics from Lin et al. 2007, Platt's targets, and refusal on thin data.

The scores and labels here are synthetic, generated to test the arithmetic only. They are not verdicts.
"""

from __future__ import annotations

import math
import random

from chaser_agent.agent import calibration, objective


def test_sigmoids_are_finite_and_symmetric_at_extremes() -> None:
    for f in (objective.sigmoid, calibration.stable_sigmoid):
        assert f(-1000.0) == 0.0 or 0.0 <= f(-1000.0) < 1e-300
        assert f(1000.0) == 1.0
        assert abs(f(0.0) - 0.5) < 1e-15
        assert abs(f(2.3) + f(-2.3) - 1.0) < 1e-12


def test_current_score_is_unchanged_by_the_stable_sigmoid() -> None:
    for z in (-8.4, -1.6, 0.0, 0.405, 3.4):
        assert abs(objective.sigmoid(z) - 1.0 / (1.0 + math.exp(-z))) < 1e-12


def test_platt_targets_follow_the_paper() -> None:
    t = calibration.platt_targets([1, 1, 0])
    assert t == [3 / 4, 3 / 4, 1 / 3]


def test_it_refuses_on_the_real_count_today() -> None:
    report = calibration.evaluate([-2.0], [0])
    assert report["ready"] is False and report["calibrated"] is False and report["fit"] is None
    assert any("accepted" in r for r in report["reasons"])


def test_separable_data_does_not_diverge() -> None:
    z = [-3.0 + 0.1 * i for i in range(30)] + [1.0 + 0.1 * i for i in range(30)]
    y = [0] * 30 + [1] * 30
    fit = calibration.fit_platt(z, y)
    assert math.isfinite(fit.a) and math.isfinite(fit.b) and fit.a < 0
    assert all(math.isfinite(fit.predict(v)) for v in (-1e6, 0.0, 1e6))


def test_extreme_scores_stay_finite() -> None:
    z = [-1000.0, -500.0, 500.0, 1000.0] * 15
    y = [0, 0, 1, 1] * 15
    fit = calibration.fit_platt(z, y)
    assert math.isfinite(calibration._objective(fit.a, fit.b, z, calibration.platt_targets(y)))


def test_it_recovers_a_known_map_and_reports_held_out_metrics() -> None:
    rng = random.Random(7)
    z = [rng.uniform(-4, 4) for _ in range(300)]
    true_a, true_b = -2.0, 0.5
    y = [1 if rng.random() < calibration.stable_sigmoid(-(true_a * v + true_b)) else 0 for v in z]
    fit = calibration.fit_platt(z, y)
    assert fit.converged and abs(fit.a - true_a) < 0.5 and abs(fit.b - true_b) < 0.5
    report = calibration.evaluate(z, y)
    assert report["calibrated"] is True and report["ready"] is True
    held = report["held_out"]
    assert held["platt"]["nll"] < held["acceptance_rate"]["nll"]
    # One monotone map keeps the ranking; held-out predictions pooled from three folds' maps can differ slightly.
    assert abs(held["platt"]["auroc"] - held["current_fixed_map"]["auroc"]) < 0.01
    single = calibration.fit_platt(z, y)
    ranks = sorted(range(len(z)), key=lambda i: z[i])
    assert all(single.predict(z[ranks[i]]) <= single.predict(z[ranks[i + 1]]) + 1e-12 for i in range(len(z) - 1))
    assert sum(b["count"] for b in held["platt"]["bins"]) == len(y)
