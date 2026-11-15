import torch
import torch.nn.functional as F
from torch_geometric.datasets import EllipticBitcoinDataset
from torch_geometric.nn import SAGEConv
from sklearn.metrics import (precision_score, recall_score,
                             f1_score, average_precision_score)

torch.manual_seed(42)
data = EllipticBitcoinDataset(root="data/elliptic")[0]


class GraphSAGE(torch.nn.Module):
    def __init__(self, in_dim, hidden, out_dim):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.conv2 = SAGEConv(hidden, out_dim)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.3, training=self.training)
        return self.conv2(x, edge_index)


model = GraphSAGE(data.num_features, 64, 2)
optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=5e-4)

y_train = data.y[data.train_mask]
pos = (y_train == 1).sum().item()
neg = (y_train == 0).sum().item()
class_weight = torch.tensor([1.0, neg / pos])

for epoch in range(1, 201):
    model.train()
    optimizer.zero_grad()
    out = model(data.x, data.edge_index)
    loss = F.cross_entropy(out[data.train_mask], y_train, weight=class_weight)
    loss.backward()
    optimizer.step()
    if epoch % 20 == 0:
        print(f"Epoch {epoch:3d} | loss {loss.item():.4f}")

model.eval()
with torch.no_grad():
    out = model(data.x, data.edge_index)
    proba = F.softmax(out, dim=1)[:, 1][data.test_mask].numpy()

y_test = data.y[data.test_mask].numpy()
pred = (proba >= 0.5).astype(int)

print("Precision (illicit):", round(precision_score(y_test, pred), 4))
print("Recall (illicit):   ", round(recall_score(y_test, pred), 4))
print("F1 (illicit):       ", round(f1_score(y_test, pred), 4))
print("PR-AUC:             ", round(average_precision_score(y_test, proba), 4))