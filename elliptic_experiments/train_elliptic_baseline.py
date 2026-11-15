from torch_geometric.datasets import EllipticBitcoinDataset
from xgboost import XGBClassifier
from sklearn.metrics import (precision_score, recall_score,
                             f1_score, average_precision_score)

data = EllipticBitcoinDataset(root="data/elliptic")[0]

X = data.x.numpy()
y = data.y.numpy()
train_idx = data.train_mask.numpy()
test_idx = data.test_mask.numpy()

X_train, y_train = X[train_idx], y[train_idx]
X_test, y_test = X[test_idx], y[test_idx]

pos = (y_train == 1).sum()
neg = (y_train == 0).sum()

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=neg / pos,
    eval_metric="logloss",
    random_state=42,
)
model.fit(X_train, y_train)

proba = model.predict_proba(X_test)[:, 1]
pred = (proba >= 0.5).astype(int)

print("Precision (illicit):", round(precision_score(y_test, pred), 4))
print("Recall (illicit):   ", round(recall_score(y_test, pred), 4))
print("F1 (illicit):       ", round(f1_score(y_test, pred), 4))
print("PR-AUC:             ", round(average_precision_score(y_test, proba), 4))