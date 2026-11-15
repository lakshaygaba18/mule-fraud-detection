from torch_geometric.datasets import EllipticBitcoinDataset
from xgboost import XGBClassifier
from sklearn.metrics import (precision_score, recall_score,
                             f1_score, average_precision_score)

data = EllipticBitcoinDataset(root="data/elliptic")[0]
X = data.x.numpy()
y = data.y.numpy()
tr = data.train_mask.numpy()
te = data.test_mask.numpy()

feature_sets = {
    "local only (first 93)": slice(0, 93),
    "all 165 (local + aggregated)": slice(0, 165),
}

for name, cols in feature_sets.items():
    X_tr, y_tr = X[tr][:, cols], y[tr]
    X_te, y_te = X[te][:, cols], y[te]
    model = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        scale_pos_weight=(y_tr == 0).sum() / (y_tr == 1).sum(),
        eval_metric="logloss", random_state=42,
    )
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    print(f"\n{name}")
    print("  Precision:", round(precision_score(y_te, pred), 4))
    print("  Recall:   ", round(recall_score(y_te, pred), 4))
    print("  F1:       ", round(f1_score(y_te, pred), 4))
    print("  PR-AUC:   ", round(average_precision_score(y_te, proba), 4))