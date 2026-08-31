"""
score_adversarial_with_v2.py

Tests gnn_model_v2.pt (retrained on baseline+structuring) against the
adversarial batch, which v2 has NEVER seen during training. This checks
genuine generalization: did learning one new fraud pattern (structuring)
help the model catch a DIFFERENT evasion attempt (adversarial braiding)?

Compare this recall directly against v1's 67.1% on the same batch
(from score_adversarial_batch.py) to see if retraining actually helped.
"""
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from sklearn.preprocessing import StandardScaler

COMBINED_FEATURES_FILE = "combined_account_features.csv"  # what v2 was trained on
ADVERSARIAL_TRANSACTIONS_FILE = "adversarial_transactions.csv"
ADVERSARIAL_FEATURES_FILE = "adversarial_account_features.csv"
MODEL_FILE = "gnn_model_v2.pt"
OUTPUT_FILE = "adversarial_account_risk_report_v2.csv"

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


def main():
    combined_features = pd.read_csv(COMBINED_FEATURES_FILE)
    scaler = StandardScaler()
    scaler.fit(combined_features[FEATURE_COLS].values)

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
    adv_features.to_csv(OUTPUT_FILE, index=False)

    flagged = adv_features[adv_features["risk_score"] >= 50]
    actual_fraud = adv_features[adv_features["label"] == 1]
    caught = flagged[flagged["label"] == 1]

    recall = len(caught) / max(len(actual_fraud), 1)
    print(f"=== gnn_model_v2 (retrained) on adversarial batch (genuinely unseen) ===")
    print(f"Actual fraud/mule accounts: {len(actual_fraud)}")
    print(f"Flagged (risk_score >= 50): {len(flagged)}")
    print(f"True positives: {len(caught)}")
    print(f"Recall: {recall:.1%}")
    print(f"\n(Compare to v1's 67.1% recall on this same adversarial batch)")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()