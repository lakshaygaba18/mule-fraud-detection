"""
add_topology_feature.py

Adds ONE new structural feature: is_passthrough -- accounts with exactly
one inbound and one outbound transaction (in_degree == 1 and out_degree == 1).

Why this matters: your old mule-ring pattern is a STAR topology (one mule
receives from 5-20 senders, then fans out to 1-4 cash-outs) -- high
in_degree. Your new "structuring" pattern is a CHAIN topology (money hops
through several accounts, each handling exactly one in + one out) -- these
middle-of-chain accounts look almost like ordinary low-activity accounts on
every feature the model was trained on, which is exactly why they slip
through.

This feature doesn't get fed to the GNN (no retraining needed) -- it's a
pure MONITORING signal: if the proportion of pass-through accounts in the
traffic suddenly rises, that's a structural shift worth flagging even when
in_degree/velocity_hours/risk_score all look "stable" in aggregate.
"""
import pandas as pd

BASELINE_FEATURES_FILE = "account_features.csv"
DRIFT_FEATURES_FILE = "drift_account_features.csv"


def add_feature(path):
    df = pd.read_csv(path)
    df["is_passthrough"] = ((df["in_degree"] == 1) & (df["out_degree"] == 1)).astype(int)
    df.to_csv(path, index=False)
    pct = df["is_passthrough"].mean() * 100
    print(f"{path}: {df['is_passthrough'].sum()} pass-through accounts ({pct:.2f}% of {len(df)})")
    return df


def main():
    add_feature(BASELINE_FEATURES_FILE)
    add_feature(DRIFT_FEATURES_FILE)
    print("\nDone. Re-run run_drift_check.py -- it will now also compare "
          "is_passthrough rates between baseline and current traffic.")


if __name__ == "__main__":
    main()