"""
drift_monitor.py

The "self-awareness" layer of the fraud agent: watches whether the model's
input-feature distributions, its score distribution, and its explanation
patterns are shifting away from the baseline it was trained/validated on --
WITHOUT needing new ground-truth labels (which always lag in production).

Plug-in point: swap `baseline_df` / `current_df` for the real outputs of
your GNN + explain.py pipeline (account_risk_report.csv with a risk_score
column). Nothing else here changes.

Core metrics:
- PSI (Population Stability Index)   -> per-feature and on risk_score itself
- Jensen-Shannon divergence           -> symmetric, bounded alternative to KL,
                                          used for the explanation-tag drift
- A single DriftReport object you can render straight into a dashboard panel
  or a compliance log entry.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# PSI thresholds (industry-standard rule of thumb, used as-is by most banks'
# model-risk teams -- this is why PSI is the safer choice for a compliance-
# facing dashboard vs a bare KL-divergence number that has no fixed scale)
# ---------------------------------------------------------------------------
PSI_STABLE = 0.10
PSI_MODERATE = 0.25
# < PSI_STABLE            -> no significant shift
# PSI_STABLE..PSI_MODERATE -> moderate shift, worth watching
# > PSI_MODERATE           -> major shift, retrain/investigate


def _bin_edges(reference: np.ndarray, n_bins: int = 10) -> np.ndarray:
    """Quantile-based bin edges from the reference (baseline) distribution."""
    qs = np.linspace(0, 1, n_bins + 1)
    edges = np.unique(np.quantile(reference, qs))
    if len(edges) < 3:
        # degenerate (near-constant) feature -- fall back to equal-width bins
        lo, hi = reference.min(), reference.max()
        edges = np.linspace(lo, hi if hi > lo else lo + 1, n_bins + 1)
    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges


def population_stability_index(baseline: pd.Series, current: pd.Series, n_bins: int = 10) -> float:
    """
    PSI = sum( (cur% - base%) * ln(cur% / base%) ) over bins.
    Bins are defined by the BASELINE distribution's quantiles, then both
    distributions are counted into those same bins -- this is what makes it
    sensitive to the current data moving into regions the model rarely saw.
    """
    baseline = baseline.dropna().astype(float).values
    current = current.dropna().astype(float).values
    if len(baseline) == 0 or len(current) == 0:
        return float("nan")

    edges = _bin_edges(baseline, n_bins)

    base_counts, _ = np.histogram(baseline, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)

    eps = 1e-6  # avoid div-by-zero / log(0) on empty bins
    base_pct = base_counts / base_counts.sum() + eps
    cur_pct = cur_counts / cur_counts.sum() + eps

    psi = np.sum((cur_pct - base_pct) * np.log(cur_pct / base_pct))
    return float(psi)


def jensen_shannon_divergence(p_counts: dict, q_counts: dict) -> float:
    """
    Symmetric, bounded (0..ln2) divergence between two categorical
    distributions given as {category: count} dicts. Used for explanation-tag
    drift, where categories are reason-tags rather than continuous features.
    """
    keys = sorted(set(p_counts) | set(q_counts))
    p = np.array([p_counts.get(k, 0) for k in keys], dtype=float)
    q = np.array([q_counts.get(k, 0) for k in keys], dtype=float)

    eps = 1e-9
    p = p / p.sum() + eps if p.sum() > 0 else p + eps
    q = q / q.sum() + eps if q.sum() > 0 else q + eps
    p = p / p.sum()
    q = q / q.sum()

    m = 0.5 * (p + q)
    kl_pm = np.sum(p * np.log(p / m))
    kl_qm = np.sum(q * np.log(q / m))
    return float(0.5 * kl_pm + 0.5 * kl_qm)


def psi_status(psi: float) -> str:
    if np.isnan(psi):
        return "unknown"
    if psi < PSI_STABLE:
        return "stable"
    if psi < PSI_MODERATE:
        return "moderate_shift"
    return "major_shift"


@dataclass
class DriftReport:
    feature_psi: dict = field(default_factory=dict)
    score_psi: Optional[float] = None
    explanation_js_divergence: Optional[float] = None
    overall_status: str = "stable"
    alerts: list = field(default_factory=list)

    def summary_text(self) -> str:
        lines = [f"Overall model-drift status: {self.overall_status.upper()}"]
        if self.score_psi is not None:
            lines.append(
                f"Risk-score distribution PSI: {self.score_psi:.3f} "
                f"({psi_status(self.score_psi)})"
            )
        if self.feature_psi:
            worst = sorted(self.feature_psi.items(), key=lambda kv: -kv[1])[:3]
            lines.append("Most-drifted features:")
            for name, psi in worst:
                lines.append(f"  - {name}: PSI={psi:.3f} ({psi_status(psi)})")
        if self.explanation_js_divergence is not None:
            lines.append(
                f"Explanation-pattern divergence (JS): {self.explanation_js_divergence:.3f}"
            )
        if self.alerts:
            lines.append("Alerts:")
            for a in self.alerts:
                lines.append(f"  ! {a}")
        return "\n".join(lines)


def compute_drift_report(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    feature_cols: list,
    score_col: str = "risk_score",
    baseline_reasons: Optional[list] = None,
    current_reasons: Optional[list] = None,
) -> DriftReport:
    """
    baseline_df / current_df : account-level feature (+ score) tables, same
        schema as account_features.csv / account_risk_report.csv.
    feature_cols             : which numeric columns to check for input drift.
    score_col                : the model's output risk score column.
    baseline_reasons / current_reasons : optional lists of explanation reason
        strings (e.g. from generate_explanation()); we tag-match on a small
        fixed vocabulary to check whether the *kind* of reasoning the model
        is giving is shifting too, not just the numbers.
    """
    report = DriftReport()

    # --- 1. per-feature input drift ---
    for col in feature_cols:
        if col in baseline_df.columns and col in current_df.columns:
            psi = population_stability_index(baseline_df[col], current_df[col])
            report.feature_psi[col] = psi

    # --- 2. output (risk score) drift ---
    if score_col in baseline_df.columns and score_col in current_df.columns:
        report.score_psi = population_stability_index(baseline_df[score_col], current_df[score_col])

    # --- 3. explanation-pattern drift (optional) ---
    if baseline_reasons is not None and current_reasons is not None:
        tag_vocab = [
            "different senders", "forwarded funds", "passed on",
            "incoming payments arrived within", "sudden payment",
            "subtler behavioral signals",
        ]

        def tag_counts(reasons):
            counts = {t: 0 for t in tag_vocab}
            for r in reasons:
                for t in tag_vocab:
                    if t in r:
                        counts[t] += 1
            return counts

        report.explanation_js_divergence = jensen_shannon_divergence(
            tag_counts(baseline_reasons), tag_counts(current_reasons)
        )

    # --- 4. roll up into overall status + alerts ---
    worst_feature_psi = max(report.feature_psi.values(), default=0.0)
    statuses = [psi_status(worst_feature_psi)]
    if report.score_psi is not None:
        statuses.append(psi_status(report.score_psi))

    if "major_shift" in statuses:
        report.overall_status = "major_shift"
    elif "moderate_shift" in statuses:
        report.overall_status = "moderate_shift"
    else:
        report.overall_status = "stable"

    if report.score_psi is not None and psi_status(report.score_psi) != "stable":
        report.alerts.append(
            f"Risk-score distribution has shifted (PSI={report.score_psi:.3f}) -- "
            "the model may be scoring current traffic on patterns it wasn't "
            "validated on. Recommend a labeled-sample audit before trusting "
            "new low/high scores blindly."
        )

    for name, psi in report.feature_psi.items():
        if psi_status(psi) == "major_shift":
            report.alerts.append(
                f"Input feature '{name}' has drifted sharply (PSI={psi:.3f}) -- "
                "check if a new account/transaction pattern has entered the data."
            )

    if report.explanation_js_divergence is not None and report.explanation_js_divergence > 0.15:
        report.alerts.append(
            f"The model's *reasoning* is changing shape (JS divergence="
            f"{report.explanation_js_divergence:.3f}), even before scores "
            "necessarily shift -- often an earlier warning sign than score PSI alone."
        )

    return report


# ---------------------------------------------------------------------------
# Self-test: run this file directly (`python drift_monitor.py`) to confirm
# everything imports and works, using fake data -- no dependency on your
# real CSVs yet. Step 4 (run_drift_check.py) will call the same
# compute_drift_report() function on your real account_risk_report.csv.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    rng = np.random.default_rng(42)

    # fake "baseline" -- what the model was validated on
    baseline_df = pd.DataFrame({
        "in_degree": rng.poisson(5, 500),
        "velocity_hours": rng.exponential(200, 500),
        "risk_score": rng.uniform(0, 40, 500),
    })

    # fake "current" -- deliberately shifted, to prove the module can catch it
    current_df = pd.DataFrame({
        "in_degree": rng.poisson(9, 500),          # shifted up
        "velocity_hours": rng.exponential(40, 500), # much faster now
        "risk_score": rng.uniform(0, 70, 500),      # scores trending higher
    })

    report = compute_drift_report(
        baseline_df, current_df,
        feature_cols=["in_degree", "velocity_hours"],
        score_col="risk_score",
    )

    print("=== drift_monitor.py self-test ===")
    print(report.summary_text())
    print("\nIf you see PSI values and alerts above (not an error), the module works.")