"""
score_adversarial_batch.py

Same approach as score_current_batch.py -- loads the ALREADY-TRAINED
gnn_model.pt (no retraining) and scores the adversarial batch with it.
"""
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from sklearn.preprocessing import StandardScaler

BASELINE_FEATURES_FILE = "account_features.csv"
ADVERSARIAL_TRANSACTIONS_FILE = "adversarial_transactions.csv"
ADVERSARIAL_FEATURES_FILE = "adversarial_account_features.csv"
MODEL_FILE = "gnn_model.pt"
OUTPUT_FILE = "adversarial_account_risk_report.csv"

FEATURE_COLS = [
    "in_degree", "out_degree", "unique_senders", "unique_receivers",
    "pass_through_ratio", "velocity_hours", "in_span_hours",
]


class GraphSAGE(torch.nn.Module):
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
    baseline_features = pd.read_csv(BASELINE_FEATURES_FILE)
    scaler = StandardScaler()
    scaler.fit(baseline_features[FEATURE_COLS].values)

    tx = pd.read_csv(ADVERSARIAL_TRANSACTIONS_FILE)
    adv_features = pd.read_csv(ADVERSARIAL_FEATURES_FILE)

    account_ids = adv_features["account_id"].tolist()
    id_to_idx = {acc: i for i, acc in enumerate(account_ids)}

    edge_index = torch.tensor([
        [id_to_idx[s] for s in tx["sender"]],
        [id_to_idx[r] for r in tx["receiver"]],
    ], dtype=torch.long)

    X = adv_features[FEATURE_COLS].values
    X_scaled = scaler.transform(X)
    x = torch.tensor(X_scaled, dtype=torch.float)

    data = Data(x=x, edge_index=edge_index)

    model = GraphSAGE(in_channels=len(FEATURE_COLS))
    model.load_state_dict(torch.load(MODEL_FILE))
    model.eval()

    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)[:, 1].numpy()

    adv_features["risk_score"] = (probs * 100).round(1)
    adv_features["reason"] = adv_features.apply(generate_explanation, axis=1)
    adv_features.to_csv(OUTPUT_FILE, index=False)

    flagged = adv_features[adv_features["risk_score"] >= 50]
    actual_fraud = adv_features[adv_features["label"] == 1]
    caught = flagged[flagged["label"] == 1]

    print(f"Scored {len(adv_features)} accounts from the adversarial batch")
    print(f"Actual fraud/mule accounts in this batch: {len(actual_fraud)}")
    print(f"Accounts the (unretrained) model flagged as risk_score >= 50: {len(flagged)}")
    print(f"  - of which actually fraud (true positives): {len(caught)}")
    print(f"  - recall on this ADVERSARIAL batch: {len(caught) / max(len(actual_fraud), 1):.1%}")
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()