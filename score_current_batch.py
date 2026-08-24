"""
score_current_batch.py

Loads your ALREADY-TRAINED gnn_model.pt (from train_gnn.py) and scores the
NEW drift batch (drift_account_features.csv / drift_transactions.csv) with
it -- WITHOUT retraining. This simulates "the model deployed in production,
seeing next month's traffic."

Important: the scaler must be fit on the ORIGINAL baseline features (the
same data the model was trained on), then applied to the new batch. Fitting
a fresh scaler on the new batch would silently hide drift instead of
exposing it.

Output: drift_account_risk_report.csv (same shape as account_risk_report.csv)
        with a risk_score column, plus a `reason` column with explanations.
"""
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from sklearn.preprocessing import StandardScaler

BASELINE_FEATURES_FILE = "account_features.csv"      # what the model was trained on
DRIFT_TRANSACTIONS_FILE = "drift_transactions.csv"
DRIFT_FEATURES_FILE = "drift_account_features.csv"
MODEL_FILE = "gnn_model.pt"
OUTPUT_FILE = "drift_account_risk_report.csv"

FEATURE_COLS = [
    "in_degree", "out_degree", "unique_senders", "unique_receivers",
    "pass_through_ratio", "velocity_hours", "in_span_hours",
]


class GraphSAGE(torch.nn.Module):
    """Must match train_gnn.py's architecture exactly, or load_state_dict fails."""
    def __init__(self, in_channels, hidden_channels=64, out_channels=2):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv2(x, edge_index)
        return x


def generate_explanation(row):
    """Same reasoning rules as explain.py, so reason-tag drift is comparable."""
    reasons = []
    if row["in_degree"] >= 5:
        reasons.append(f"received money from {row['unique_senders']} different senders")
    if row["velocity_hours"] < 100:
        reasons.append(f"forwarded funds onward within {row['velocity_hours']:.1f} hours of receiving them")
    if row["pass_through_ratio"] > 0.7:
        reasons.append(f"passed on {row['pass_through_ratio']*100:.0f}% of everything it received")
    if row["in_span_hours"] < 48 and row["in_degree"] >= 3:
        reasons.append(f"all incoming payments arrived within a {row['in_span_hours']:.1f}-hour window")
    if row["in_degree"] <= 1 and row["out_degree"] == 0 and row["avg_in_amount"] > 3000:
        reasons.append(
            f"received a single sudden payment of ~₹{row['avg_in_amount']:.0f} with no prior "
            "transaction history and no outbound activity yet -- consistent with a fresh cash-out account"
        )
    if not reasons:
        reasons.append("flagged by the model based on a combination of subtler behavioral signals")
    return "; ".join(reasons)


def main():
    # --- fit scaler on BASELINE data (what the model actually learned from) ---
    baseline_features = pd.read_csv(BASELINE_FEATURES_FILE)
    scaler = StandardScaler()
    scaler.fit(baseline_features[FEATURE_COLS].values)

    # --- build graph for the NEW drift batch ---
    tx = pd.read_csv(DRIFT_TRANSACTIONS_FILE)
    drift_features = pd.read_csv(DRIFT_FEATURES_FILE)

    account_ids = drift_features["account_id"].tolist()
    id_to_idx = {acc: i for i, acc in enumerate(account_ids)}

    edge_index = torch.tensor([
        [id_to_idx[s] for s in tx["sender"]],
        [id_to_idx[r] for r in tx["receiver"]],
    ], dtype=torch.long)

    X = drift_features[FEATURE_COLS].values
    X_scaled = scaler.transform(X)  # same scaler as training, NOT refit here
    x = torch.tensor(X_scaled, dtype=torch.float)

    data = Data(x=x, edge_index=edge_index)

    # --- load the already-trained model (no retraining) ---
    model = GraphSAGE(in_channels=len(FEATURE_COLS))
    model.load_state_dict(torch.load(MODEL_FILE))
    model.eval()

    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)[:, 1].numpy()

    drift_features["risk_score"] = (probs * 100).round(1)
    drift_features["reason"] = drift_features.apply(generate_explanation, axis=1)
    drift_features.to_csv(OUTPUT_FILE, index=False)

    # quick sanity check: how well does the OLD model catch the NEW pattern?
    flagged = drift_features[drift_features["risk_score"] >= 50]
    actual_fraud = drift_features[drift_features["label"] == 1]
    caught = flagged[flagged["label"] == 1]

    print(f"Scored {len(drift_features)} accounts from the drift batch")
    print(f"Actual fraud/mule accounts in this batch: {len(actual_fraud)}")
    print(f"Accounts the (unretrained) model flagged as risk_score >= 50: {len(flagged)}")
    print(f"  - of which actually fraud (true positives): {len(caught)}")
    print(f"  - recall on this NEW batch: {len(caught) / max(len(actual_fraud), 1):.1%}")
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()