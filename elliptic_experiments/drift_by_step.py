import numpy as np
import pandas as pd
from torch_geometric.datasets import EllipticBitcoinDataset

data = EllipticBitcoinDataset(root="data/elliptic")[0]
X = data.x.numpy()
ts = pd.read_csv("data/elliptic/raw/elliptic_txs_features.csv", header=None)[1].values.copy()


def psi(expected, actual, bins=10):
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    inner = edges[1:-1]
    e = np.bincount(np.searchsorted(inner, expected, side="right"), minlength=len(inner) + 1)
    a = np.bincount(np.searchsorted(inner, actual, side="right"), minlength=len(inner) + 1)
    e = np.clip(e / len(expected), 1e-4, None)
    a = np.clip(a / len(actual), 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


baseline = X[ts <= 34]

print("step | mean PSI | features with PSI > 0.25")
for t in range(30, 50):
    cur = X[ts == t]
    scores = [psi(baseline[:, j], cur[:, j]) for j in range(X.shape[1])]
    print(f"{t:4d} | {np.mean(scores):8.3f} | {sum(s > 0.25 for s in scores):3d} / {X.shape[1]}")