import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.datasets import EllipticBitcoinDataset
from torch_geometric.nn import SAGEConv
from sklearn.metrics import (precision_score, recall_score,
                             f1_score, average_precision_score)

data = EllipticBitcoinDataset(root="data/elliptic")[0]

# time step of every node (column 1 of the raw features file)
ts = pd.read_csv("data/elliptic/raw/elliptic_txs_features.csv", header=None)[1].values
ts = torch.from_numpy(ts)

labeled = data.y != 2
train_mask = (ts <= 24) & labeled
val_mask = (ts >= 25) & (ts <= 34) & labeled
test_mask = data.test_mask


class GraphSAGE(torch.nn.Module):
    def __init__(self, in_dim, hidden, out_dim):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.conv2 = SAGEConv(hidden, out_dim)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.5, training=self.training)
        return self.conv2(x, edge_index)


def probs(model, x, mask):
    model.eval()
    with torch.no_grad():
        out = model(x, data.edge_index)
    return F.softmax(out, dim=1)[:, 1][mask].numpy()


def run(n_feats, name):
    torch.manual_seed(42)
    x = data.x[:, :n_feats]
    model = GraphSAGE(n_feats, 64, 2)
    opt = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=5e-4)

    y_tr = data.y[train_mask]
    w = torch.tensor([1.0, (y_tr == 0).sum().item() / (y_tr == 1).sum().item()])
    y_val = data.y[val_mask].numpy()
    y_te = data.y[test_mask].numpy()

    best_ap, best_state, best_epoch, bad = 0.0, None, 0, 0
    for epoch in range(1, 401):
        model.train()
        opt.zero_grad()
        out = model(x, data.edge_index)
        loss = F.cross_entropy(out[train_mask], y_tr, weight=w)
        loss.backward()
        opt.step()
        if epoch % 5 == 0:
            ap = average_precision_score(y_val, probs(model, x, val_mask))
            if ap > best_ap:
                best_ap, best_epoch, bad = ap, epoch, 0
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            else:
                bad += 1
                if bad >= 10:
                    break

    model.load_state_dict(best_state)

    # choose the decision threshold on validation data, not on test data
    p_val = probs(model, x, val_mask)
    thrs = np.linspace(0.05, 0.95, 19)
    f1s = [f1_score(y_val, (p_val >= t).astype(int), zero_division=0) for t in thrs]
    thr = float(thrs[int(np.argmax(f1s))])

    p_te = probs(model, x, test_mask)
    pred = (p_te >= thr).astype(int)
    print(f"\n{name}  (best epoch {best_epoch}, val PR-AUC {best_ap:.4f}, threshold {thr:.2f})")
    print("  Precision:", round(precision_score(y_te, pred, zero_division=0), 4))
    print("  Recall:   ", round(recall_score(y_te, pred), 4))
    print("  F1:       ", round(f1_score(y_te, pred), 4))
    print("  PR-AUC:   ", round(average_precision_score(y_te, p_te), 4))


run(93, "GraphSAGE, local features only")
run(165, "GraphSAGE, all features")