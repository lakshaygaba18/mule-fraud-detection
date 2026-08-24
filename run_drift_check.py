"""
run_drift_check.py

THE final piece: compares your ORIGINAL baseline (account_features.csv +
account_risk_report.csv, from training time) against the NEW drift batch
(drift_account_features.csv + drift_account_risk_report.csv, from
"production" time) and prints a single, dashboard-ready drift report.

This is the "self-awareness" moment of the whole project: the system
noticing its own environment has shifted, WITHOUT being told the recall
number you just saw. In a real deployment you would run this on a schedule
(e.g. nightly) with no labels available at all.
"""
import pandas as pd
from drift_monitor import compute_drift_report
from score_current_batch import generate_explanation  # same reasoning fn, reused

BASELINE_FEATURES_FILE = "account_features.csv"
BASELINE_SCORES_FILE = "account_risk_report.csv"       # from your GNN/explain.py run
CURRENT_FEATURES_FILE = "drift_account_features.csv"
CURRENT_SCORES_FILE = "drift_account_risk_report.csv"  # from score_current_batch.py

FEATURE_COLS = [
    "in_degree", "out_degree", "unique_senders", "unique_receivers",
    "pass_through_ratio", "velocity_hours", "in_span_hours",
    "is_passthrough",  # structural/topology signal -- catches chain-style
                       # fraud that per-node score/feature drift misses
]


def main():
    baseline_features = pd.read_csv(BASELINE_FEATURES_FILE)
    baseline_scores = pd.read_csv(BASELINE_SCORES_FILE)
    current_scores = pd.read_csv(CURRENT_SCORES_FILE)  # already has features + risk_score + reason

    # baseline_features has the feature columns; baseline_scores has risk_score.
    # Merge them so drift_monitor can check both feature drift AND score drift
    # against the SAME baseline table.
    baseline_df = baseline_features.merge(
        baseline_scores[["account_id", "risk_score"]], on="account_id", how="inner"
    )
    current_df = current_scores  # already merged in score_current_batch.py

    # generate baseline reasons using the same rule-based explainer, so the
    # explanation-pattern comparison is apples-to-apples with the current batch
    baseline_df["reason"] = baseline_df.apply(generate_explanation, axis=1)

    report = compute_drift_report(
        baseline_df=baseline_df,
        current_df=current_df,
        feature_cols=FEATURE_COLS,
        score_col="risk_score",
        baseline_reasons=baseline_df["reason"].tolist(),
        current_reasons=current_df["reason"].tolist(),
    )

    print("=" * 70)
    print("FRAUD MODEL -- DRIFT MONITORING REPORT")
    print("=" * 70)
    print(report.summary_text())
    print("=" * 70)

    if report.overall_status != "stable":
        print(
            "\nRECOMMENDATION: This system detected the shift shown above "
            "WITHOUT using any ground-truth fraud labels from the new batch. "
            "In production this report would fire before a human-reviewed "
            "recall drop is even visible -- flag for a labeled-sample audit "
            "and a retraining cycle."
        )
    else:
        print("\nNo significant drift detected -- model appears stable on current traffic.")


if __name__ == "__main__":
    main()