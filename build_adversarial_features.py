"""
build_adversarial_features.py

Same feature-engineering logic as build_features.py / build_drift_features.py,
pointed at the adversarial batch. Also computes is_passthrough directly
(instead of needing a separate add_topology_feature.py run) since we know
upfront this is the exact signal we're testing for evasion.
"""
import pandas as pd
import numpy as np

INPUT_FILE = "adversarial_transactions.csv"
OUTPUT_FILE = "adversarial_account_features.csv"


def load_data():
    tx = pd.read_csv(INPUT_FILE, parse_dates=["timestamp"])
    return tx


def get_account_labels(tx):
    sender_labels = tx[["sender", "sender_label"]].rename(
        columns={"sender": "account_id", "sender_label": "label"}
    )
    receiver_labels = tx[["receiver", "receiver_label"]].rename(
        columns={"receiver": "account_id", "receiver_label": "label"}
    )
    all_labels = pd.concat([sender_labels, receiver_labels])
    return all_labels.groupby("account_id")["label"].max().reset_index()


def build_features(tx: pd.DataFrame) -> pd.DataFrame:
    accounts = get_account_labels(tx)

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
            first_in = in_tx["timestamp"].min()
            last_out = out_tx["timestamp"].max()
            velocity_hours = max((last_out - first_in).total_seconds() / 3600.0, 0.0)
        else:
            velocity_hours = np.nan

        if in_degree >= 2:
            in_span_hours = (in_tx["timestamp"].max() - in_tx["timestamp"].min()).total_seconds() / 3600.0
        else:
            in_span_hours = np.nan

        avg_in_amount = in_tx["amount"].mean() if in_degree > 0 else 0.0
        avg_out_amount = out_tx["amount"].mean() if out_degree > 0 else 0.0

        rows.append({
            "account_id": account_id,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "unique_senders": unique_senders,
            "unique_receivers": unique_receivers,
            "total_in": total_in,
            "total_out": total_out,
            "pass_through_ratio": pass_through_ratio,
            "velocity_hours": velocity_hours,
            "in_span_hours": in_span_hours,
            "avg_in_amount": avg_in_amount,
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
    tx = load_data()
    features = build_features(tx)
    features.to_csv(OUTPUT_FILE, index=False)

    n_fraud = (features.label == 1).sum()
    n_passthrough = features["is_passthrough"].sum()
    print(f"Built features for {len(features)} accounts")
    print(f"  - normal:     {len(features) - n_fraud}")
    print(f"  - mule/fraud: {n_fraud}")
    print(f"  - is_passthrough accounts: {n_passthrough} "
          f"({n_passthrough / len(features) * 100:.2f}%)")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()