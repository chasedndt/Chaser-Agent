"""Offline Platt calibration for the objective score, refusing until there are enough real verdicts.

Chaser Agent's score is sigmoid(z) with z = BIAS + w . x and hand-set w. That is Platt's form with
A = -1, B = 0 fixed (Platt 1999, eq. 9; z read as -f). This module is the honest route to a calibrated
reading of z, and nothing more:

- It fits a probability map p = 1 / (1 + exp(A z + B)) on frozen scores. It does not refit the
  feature weights, judge factual correctness, or change when the agent stops.
- What it predicts is the label it is given: the owner's Accept/Reject on a reply, not truth.
- Targets are Platt's smoothed ones, t+ = (N+ + 1)/(N+ + 2) and t- = 1/(N- + 2) (Platt 1999, eqs. 13-14),
  so a separable or tiny sample can't push A to infinity.
- The fit is Lin, Lin and Weng's Newton method with backtracking line search and the sign-split,
  overflow-free objective (Lin et al. 2007, Algorithm 1, pp. 4-6, Appendix C constants).
- Quality is measured only on held-out folds (Platt 1999 p. 6; Guo et al. 2017 sec. 4), against two
  baselines: the current fixed map and the plain acceptance rate. Reported: NLL, Brier, ECE with
  equal-count bins and their counts, and AUROC (ranking, which a monotone map can't change).
- It refuses to fit, and says why, below a minimum of each class. Meeting the minimum is a floor,
  not proof the result is valid: correlated turns, one rater and shifting tasks still apply.

Nothing here runs inside the agent loop. It reads verdicts it is handed and returns a report.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

MIN_PER_CLASS = 20
MIN_TOTAL = 40
FOLDS = 3


def stable_sigmoid(value: float) -> float:
    """1 / (1 + exp(-value)) without overflow for any finite value (Lin et al. 2007, pp. 5-6)."""
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    e = math.exp(value)
    return e / (1.0 + e)


def _log1pexp(value: float) -> float:
    """log(1 + exp(value)), stable for large |value|."""
    return value + math.log1p(math.exp(-value)) if value > 0 else math.log1p(math.exp(value))


def platt_targets(labels: Sequence[int]) -> list[float]:
    positives = sum(1 for y in labels if y)
    negatives = len(labels) - positives
    hi, lo = (positives + 1.0) / (positives + 2.0), 1.0 / (negatives + 2.0)
    return [hi if y else lo for y in labels]


def _objective(a: float, b: float, z: Sequence[float], t: Sequence[float]) -> float:
    """Negative log likelihood of p = 1/(1+exp(a z + b)) against targets t, overflow-free."""
    total = 0.0
    for zi, ti in zip(z, t):
        f = a * zi + b
        total += ti * f + _log1pexp(-f) if f >= 0 else (ti - 1.0) * f + _log1pexp(f)
    return total


def _probability(a: float, b: float, zi: float) -> float:
    return stable_sigmoid(-(a * zi + b))


@dataclass(frozen=True)
class Fit:
    a: float
    b: float
    iterations: int
    converged: bool

    def predict(self, zi: float) -> float:
        return _probability(self.a, self.b, zi)


def fit_platt(z: Sequence[float], labels: Sequence[int], *, max_iter: int = 100, min_step: float = 1e-10,
              sigma: float = 1e-12, eps: float = 1e-5) -> Fit:
    """Lin et al. 2007 Algorithm 1: Newton direction on the Platt objective with backtracking."""
    if len(z) != len(labels) or not z:
        raise ValueError("scores and labels must be non-empty and the same length")
    t = platt_targets(labels)
    positives = sum(1 for y in labels if y)
    a, b = 0.0, math.log((len(labels) - positives + 1.0) / (positives + 1.0))
    value = _objective(a, b, z, t)
    for iteration in range(1, max_iter + 1):
        h11 = h22 = sigma
        h21 = g1 = g2 = 0.0
        for zi, ti in zip(z, t):
            p = _probability(a, b, zi)
            q = 1.0 - p
            d2 = p * q
            h11 += zi * zi * d2
            h22 += d2
            h21 += zi * d2
            d1 = ti - p
            g1 += zi * d1
            g2 += d1
        if abs(g1) < eps and abs(g2) < eps:
            return Fit(a, b, iteration, True)
        det = h11 * h22 - h21 * h21
        da = -(h22 * g1 - h21 * g2) / det
        db = -(-h21 * g1 + h11 * g2) / det
        gd = g1 * da + g2 * db
        step = 1.0
        while step >= min_step:
            na, nb = a + step * da, b + step * db
            new = _objective(na, nb, z, t)
            if new < value + 1e-4 * step * gd:
                a, b, value = na, nb, new
                break
            step /= 2.0
        else:
            return Fit(a, b, iteration, False)
    return Fit(a, b, max_iter, False)


def _metrics(probabilities: Sequence[float], labels: Sequence[int], bins: int) -> dict:
    n = len(labels)
    eps = 1e-15
    nll = -sum(math.log(max(p, eps)) if y else math.log(max(1.0 - p, eps)) for p, y in zip(probabilities, labels)) / n
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / n
    order = sorted(range(n), key=lambda i: probabilities[i])
    groups = [order[i * n // bins:(i + 1) * n // bins] for i in range(bins)]
    table, ece = [], 0.0
    for group in groups:
        if not group:
            continue
        conf = sum(probabilities[i] for i in group) / len(group)
        acc = sum(labels[i] for i in group) / len(group)
        ece += len(group) / n * abs(acc - conf)
        table.append({"count": len(group), "mean_probability": round(conf, 4), "accept_rate": round(acc, 4)})
    pos = [probabilities[i] for i in range(n) if labels[i]]
    neg = [probabilities[i] for i in range(n) if not labels[i]]
    auroc = (sum(1.0 if p > q else 0.5 if p == q else 0.0 for p in pos for q in neg) / (len(pos) * len(neg))) if pos and neg else None
    return {"nll": round(nll, 4), "brier": round(brier, 4), "ece_equal_count": round(ece, 4), "bins": table,
            "auroc": None if auroc is None else round(auroc, 4)}


def readiness(labels: Sequence[int]) -> dict:
    positives = sum(1 for y in labels if y)
    negatives = len(labels) - positives
    reasons = []
    if positives < MIN_PER_CLASS:
        reasons.append(f"{positives} accepted verdicts; at least {MIN_PER_CLASS} needed")
    if negatives < MIN_PER_CLASS:
        reasons.append(f"{negatives} rejected verdicts; at least {MIN_PER_CLASS} needed")
    if len(labels) < MIN_TOTAL:
        reasons.append(f"{len(labels)} verdicts in all; at least {MIN_TOTAL} needed")
    return {"ready": not reasons, "accepted": positives, "rejected": negatives, "reasons": reasons}


def evaluate(z: Sequence[float], labels: Sequence[int], *, folds: int = FOLDS) -> dict:
    """Cross-validated report. Refuses (ready=False, no fit) below the minimums."""
    ready = readiness(labels)
    if not ready["ready"]:
        return {**ready, "calibrated": False, "fit": None,
                "message": "Not enough real verdicts to calibrate; the score stays an uncalibrated process heuristic."}
    n = len(labels)
    # Deterministic, stratified folds: alternate positives and negatives across folds in input order.
    fold_of = [0] * n
    counters = {0: 0, 1: 0}
    for i, y in enumerate(labels):
        fold_of[i] = counters[int(bool(y))] % folds
        counters[int(bool(y))] += 1
    held_cal, held_fixed, held_base, held_y, iterations = [], [], [], [], []
    for k in range(folds):
        train = [i for i in range(n) if fold_of[i] != k]
        test = [i for i in range(n) if fold_of[i] == k]
        fit = fit_platt([z[i] for i in train], [labels[i] for i in train])
        iterations.append({"fold": k, "iterations": fit.iterations, "converged": fit.converged})
        rate = sum(labels[i] for i in train) / len(train)
        for i in test:
            held_cal.append(fit.predict(z[i]))
            held_fixed.append(stable_sigmoid(z[i]))
            held_base.append(rate)
            held_y.append(labels[i])
    bins = max(2, min(10, n // 10))
    final = fit_platt(list(z), list(labels))
    return {**ready, "calibrated": True, "folds": folds, "fold_fits": iterations,
            "held_out": {"platt": _metrics(held_cal, held_y, bins), "current_fixed_map": _metrics(held_fixed, held_y, bins),
                         "acceptance_rate": _metrics(held_base, held_y, bins)},
            "fit": {"a": final.a, "b": final.b, "converged": final.converged, "iterations": final.iterations},
            "message": ("Calibration map for the owner's acceptance, measured on held-out folds. It predicts Accept/Reject, "
                        "not factual correctness, and it does not change the stop threshold.")}
