import pandas as pd
from torch_geometric.datasets import EllipticBitcoinDataset
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, precision_score, recall_score

data = EllipticBitcoinDataset(root="data/elliptic")[0]
ts = pd.read_csv("data/elliptic/raw/elliptic_txs_features.csv", header=None)[1].values.copy()

X = data.x.numpy()
y = data.y.numpy()
tr = data.train_mask.numpy()
te = data.test_mask.numpy()

model = XGBClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.1,
    scale_pos_weight=(y[tr] == 0).sum() / (y[tr] == 1).sum(),
    eval_metric="logloss", random_state=42,
)
model.fit(X[tr], y[tr])
pred = (model.predict_proba(X)[:, 1] >= 0.5).astype(int)

print("step | labeled | illicit | precision | recall |   f1")
for t in range(35, 50):
    m = te & (ts == t)
    if m.sum() == 0:
        continue
    yt, pt = y[m], pred[m]
    print(f"{t:4d} | {m.sum():7d} | {(yt == 1).sum():7d} | "
          f"{precision_score(yt, pt, zero_division=0):9.3f} | "
          f"{recall_score(yt, pt, zero_division=0):6.3f} | "
          f"{f1_score(yt, pt, zero_division=0):.3f}")