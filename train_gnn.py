import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler

TRANSACTIONS_FILE = "transactions.csv"
FEATURES_FILE = "account_features.csv"
MODEL_FILE = "gnn_model.pt"

FEATURE_COLS = [
    "in_degree", "out_degree", "unique_senders", "unique_receivers",
    "pass_through_ratio", "velocity_hours", "in_span_hours",
]


def build_graph():
    tx = pd.read_csv(TRANSACTIONS_FILE)
    features = pd.read_csv(FEATURES_FILE)

    account_ids = features["account_id"].tolist()
    id_to_idx = {acc: i for i, acc in enumerate(account_ids)}

    edge_index = torch.tensor([
        [id_to_idx[s] for s in tx["sender"]],
        [id_to_idx[r] for r in tx["receiver"]],
    ], dtype=torch.long)

    X = features[FEATURE_COLS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    x = torch.tensor(X_scaled, dtype=torch.float)

    y = torch.tensor(features["label"].values, dtype=torch.long)

    data = Data(x=x, edge_index=edge_index, y=y)
    return data, account_ids


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
    data, account_ids = build_graph()
    n_nodes = data.num_nodes

    idx = np.arange(n_nodes)
    train_idx, test_idx = train_test_split(
        idx, test_size=0.25, random_state=42, stratify=data.y.numpy()
    )
    train_mask = torch.zeros(n_nodes, dtype=torch.bool)
    test_mask = torch.zeros(n_nodes, dtype=torch.bool)
    train_mask[train_idx] = True
    test_mask[test_idx] = True

    model = GraphSAGE(in_channels=data.x.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)

    n_normal = (data.y[train_mask] == 0).sum().item()
    n_fraud = (data.y[train_mask] == 1).sum().item()
    class_weights = torch.tensor([1.0, n_normal / n_fraud], dtype=torch.float)

    print(f"Training on {train_mask.sum().item()} nodes, testing on {test_mask.sum().item()} nodes")
    print(f"Class weight for fraud class: {class_weights[1]:.2f}")

    model.train()
    for epoch in range(100):
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)
        loss = F.cross_entropy(out[train_mask], data.y[train_mask], weight=class_weights)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 20 == 0:
            print(f"Epoch {epoch+1:3d} | Loss: {loss.item():.4f}")

    model.eval()
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)[:, 1]
        preds = out.argmax(dim=1)

    y_test = data.y[test_mask].numpy()
    preds_test = preds[test_mask].numpy()
    probs_test = probs[test_mask].numpy()

    print("\n=== GraphSAGE results on held-out test nodes ===")
    print(classification_report(y_test, preds_test, target_names=["normal", "mule-ring"]))
    print(f"AUROC: {roc_auc_score(y_test, probs_test):.4f}")

    torch.save(model.state_dict(), MODEL_FILE)
    print(f"\nModel saved to {MODEL_FILE}")


if __name__ == "__main__":
    main()