"""
combine_training_data.py

Merges the original baseline (transactions.csv) with the structuring drift
batch (drift_transactions.csv) into one combined pool, and rebuilds account
features on it. The GNN retrained on this combined pool has now "seen"
structuring-style fraud during training.

IMPORTANT: adversarial_transactions.csv is deliberately NOT included here.
We want to test the retrained model on adversarial (a pattern it has never
seen) to check genuine generalization, not memorization. If we included it
in training too, a high recall on it would prove nothing.
"""
import pandas as pd

BASELINE_TRANSACTIONS = "transactions.csv"
STRUCTURING_TRANSACTIONS = "drift_transactions.csv"
OUTPUT_TRANSACTIONS = "combined_transactions.csv"
OUTPUT_FEATURES = "combined_account_features.csv"


def build_features(tx: pd.DataFrame) -> pd.DataFrame:
    import numpy as np

    sender_labels = tx[["sender", "sender_label"]].rename(
        columns={"sender": "account_id", "sender_label": "label"}
    )
    receiver_labels = tx[["receiver", "receiver_label"]].rename(
        columns={"receiver": "account_id", "receiver_label": "label"}
    )
    accounts = pd.concat([sender_labels, receiver_labels]).groupby("account_id")["label"].max().reset_index()

    inbound_groups = {k: v for k, v in tx.groupby("receiver")}
    outbound_groups = {k: v for k, v in tx.groupby("sender")}

    rows = []
    for account_id in accounts.account_id:
        in_tx = inbound_groups.get(account_id, pd.DataFrame(columns=tx.columns))
        out_tx = outbound_groups.get(account_id, pd.DataFrame(columns=tx.columns))

        in_degree = len(in_tx)
        out_degree = len(out_tx)
        unique_senders = in_tx["sender"].nunique()
        unique_receivers = out_tx["receiver"].nunique()

        total_in = in_tx["amount"].sum()
        total_out = out_tx["amount"].sum()
        pass_through_ratio = (total_out / total_in) if total_in > 0 else 0.0

        if in_degree > 0 and out_degree > 0:
            velocity_hours = max(
                (out_tx["timestamp"].max() - in_tx["timestamp"].min()).total_seconds() / 3600.0, 0.0
            )
        else:
            velocity_hours = float("nan")

        if in_degree >= 2:
            in_span_hours = (in_tx["timestamp"].max() - in_tx["timestamp"].min()).total_seconds() / 3600.0
        else:
            in_span_hours = float("nan")

        avg_in_amount = in_tx["amount"].mean() if in_degree > 0 else 0.0
        avg_out_amount = out_tx["amount"].mean() if out_degree > 0 else 0.0

        rows.append({
            "account_id": account_id, "in_degree": in_degree, "out_degree": out_degree,
            "unique_senders": unique_senders, "unique_receivers": unique_receivers,
            "total_in": total_in, "total_out": total_out,
            "pass_through_ratio": pass_through_ratio, "velocity_hours": velocity_hours,
            "in_span_hours": in_span_hours, "avg_in_amount": avg_in_amount,
            "avg_out_amount": avg_out_amount,
        })

    features = pd.DataFrame(rows)
    features["velocity_hours"] = features["velocity_hours"].fillna(999999)
    features["in_span_hours"] = features["in_span_hours"].fillna(999999)
    features["is_passthrough"] = (
        (features["in_degree"] == 1) & (features["out_degree"] == 1)
    ).astype(int)

    return features.merge(accounts, on="account_id")


def main():
    baseline_tx = pd.read_csv(BASELINE_TRANSACTIONS, parse_dates=["timestamp"])
    structuring_tx = pd.read_csv(STRUCTURING_TRANSACTIONS, parse_dates=["timestamp"])

    combined_tx = pd.concat([baseline_tx, structuring_tx], ignore_index=True)
    combined_tx.to_csv(OUTPUT_TRANSACTIONS, index=False)

    features = build_features(combined_tx)
    features.to_csv(OUTPUT_FEATURES, index=False)

    n_fraud = (features.label == 1).sum()
    print(f"Combined pool: {len(combined_tx)} transactions, {len(features)} accounts")
    print(f"  - normal:     {len(features) - n_fraud}")
    print(f"  - mule/fraud: {n_fraud} (includes both old-style mule rings AND structuring)")
    print(f"Saved to {OUTPUT_TRANSACTIONS} and {OUTPUT_FEATURES}")
    print("\nNote: adversarial_transactions.csv is NOT included -- it stays as")
    print("a genuinely unseen test set for checking generalization after retraining.")


if __name__ == "__main__":
    main()