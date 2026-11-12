import numpy as np
import pandas as pd
from torch_geometric.datasets import EllipticBitcoinDataset
from xgboost import XGBClassifier
from sklearn.metrics import (precision_score, recall_score,
                             f1_score, average_precision_score)

data = EllipticBitcoinDataset(root="data/elliptic")[0]
ts = pd.read_csv("data/elliptic/raw/elliptic_txs_features.csv", header=None)[1].values.copy()
X, y = data.x.numpy(), data.y.numpy()
labeled = y != 2


def fit(mask):
    yt = y[mask]
    model = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        scale_pos_weight=(yt == 0).sum() / (yt == 1).sum(),
        eval_metric="logloss", random_state=42,
    )
    model.fit(X[mask], yt)
    return model


def new_store():
    return {"y": [], "p": [], "hits": 0, "flag": 0, "pos": 0}


def update(s, yt, p):
    s["y"].append(yt)
    s["p"].append(p)
    k = int(np.ceil(0.05 * len(yt)))          # analysts review top 5% per step
    top = np.argsort(-p)[:k]
    s["hits"] += int(yt[top].sum())
    s["flag"] += k
    s["pos"] += int(yt.sum())


def summary(name, s):
    yt = np.concatenate(s["y"])
    p = np.concatenate(s["p"])
    pred = (p >= 0.5).astype(int)
    print(f"\n{name}")
    print("  Precision:", round(precision_score(yt, pred, zero_division=0), 4))
    print("  Recall:   ", round(recall_score(yt, pred), 4))
    print("  F1:       ", round(f1_score(yt, pred), 4))
    print("  PR-AUC:   ", round(average_precision_score(yt, p), 4))
    print("  Top-5% alerts: precision", round(s["hits"] / s["flag"], 4),
          "| share of all illicit caught", round(s["hits"] / s["pos"], 4))


def period_report(label, lo, hi):
    sel = [r for r in rows if lo <= r[0] <= hi]
    yt = np.concatenate([r[1] for r in sel])
    print(f"\n{label}  (illicit in window: {int(yt.sum())}, total: {len(yt)})")
    for name, idx in (("Static ", 2), ("Rolling", 3)):
        p = np.concatenate([r[idx] for r in sel])
        pred = (p >= 0.5).astype(int)
        print(f"  {name} | P {precision_score(yt, pred, zero_division=0):.3f}"
              f" | R {recall_score(yt, pred):.3f}"
              f" | F1 {f1_score(yt, pred):.3f}"
              f" | PR-AUC {average_precision_score(yt, p):.3f}")


WINDOW = 10
static_model = fit((ts <= 34) & labeled)
static, rolling = new_store(), new_store()
rows = []   # (step, y_true, static_probs, rolling_probs)

print("step | static F1 | rolling F1")
for t in range(35, 50):
    te = (ts == t) & labeled
    if te.sum() == 0:
        continue
    yt = y[te]
    rolling_model = fit((ts >= t - WINDOW) & (ts <= t - 1) & labeled)

    p_s = static_model.predict_proba(X[te])[:, 1]
    p_r = rolling_model.predict_proba(X[te])[:, 1]
    update(static, yt, p_s)
    update(rolling, yt, p_r)
    rows.append((t, yt, p_s, p_r))

    f_s = f1_score(yt, (p_s >= 0.5).astype(int), zero_division=0)
    f_r = f1_score(yt, (p_r >= 0.5).astype(int), zero_division=0)
    print(f"{t:4d} | {f_s:9.3f} | {f_r:10.3f}")

summary("Static model (trained once on steps 1-34), pooled over steps 35-49", static)
summary("Rolling model (retrained each step on last 10 steps), pooled over steps 35-49", rolling)

period_report("Before shift: steps 35-42", 35, 42)
period_report("After shift: steps 43-49", 43, 49)

def rolling_after_shift(delay, window=10):
    ys, ps = [], []
    for t in range(43, 50):
        te = (ts == t) & labeled
        if te.sum() == 0:
            continue
        tr = (ts >= t - delay - window) & (ts <= t - 1 - delay) & labeled
        m = fit(tr)
        ys.append(y[te])
        ps.append(m.predict_proba(X[te])[:, 1])
    yt, p = np.concatenate(ys), np.concatenate(ps)
    pred = (p >= 0.5).astype(int)
    print(f"  label delay {delay} steps | P {precision_score(yt, pred, zero_division=0):.3f}"
          f" | R {recall_score(yt, pred):.3f} | F1 {f1_score(yt, pred):.3f}"
          f" | PR-AUC {average_precision_score(yt, p):.3f}")


print("\nRolling model after the shift (steps 43-49), with delayed labels")
for d in (0, 2, 4):
    rolling_after_shift(d)