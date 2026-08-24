from fastapi import FastAPI, HTTPException
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from drift_monitor import compute_drift_report
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from sklearn.preprocessing import StandardScaler

app = FastAPI(
    title="Fraud Detection ML Service",
    description="ML service for fraud scoring, drift monitoring and explanations",
    version="1.0.0"
)

BASELINE_FEATURES_FILE = "account_features.csv"
DRIFT_TRANSACTIONS_FILE = "drift_transactions.csv"
DRIFT_FEATURES_FILE = "drift_account_features.csv"
MODEL_FILE = "gnn_model.pt"
BASELINE_SCORES_FILE = "account_risk_report.csv"

FEATURE_COLS = [
    "in_degree", "out_degree", "unique_senders", "unique_receivers",
    "pass_through_ratio", "velocity_hours", "in_span_hours",
]

DRIFT_MONITOR_FEATURE_COLS = FEATURE_COLS + ["is_passthrough"]


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


def score_batch():
    baseline_features = pd.read_csv(BASELINE_FEATURES_FILE)
    scaler = StandardScaler()
    scaler.fit(baseline_features[FEATURE_COLS].values)

    tx = pd.read_csv(DRIFT_TRANSACTIONS_FILE)
    drift_features = pd.read_csv(DRIFT_FEATURES_FILE)

    account_ids = drift_features["account_id"].tolist()
    id_to_idx = {acc: i for i, acc in enumerate(account_ids)}

    edge_index = torch.tensor([
        [id_to_idx[s] for s in tx["sender"]],
        [id_to_idx[r] for r in tx["receiver"]],
    ], dtype=torch.long)

    X = drift_features[FEATURE_COLS].values
    X_scaled = scaler.transform(X)
    x = torch.tensor(X_scaled, dtype=torch.float)

    data = Data(x=x, edge_index=edge_index)

    model = GraphSAGE(in_channels=len(FEATURE_COLS))
    model.load_state_dict(torch.load(MODEL_FILE))
    model.eval()

    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)[:, 1].numpy()

    drift_features["risk_score"] = (probs * 100).round(1)
    drift_features["reason"] = drift_features.apply(generate_explanation, axis=1)

    return drift_features


def build_drift_report():
    baseline_features = pd.read_csv(BASELINE_FEATURES_FILE)
    baseline_scores = pd.read_csv(BASELINE_SCORES_FILE)
    baseline_df = baseline_features.merge(
        baseline_scores[["account_id", "risk_score"]], on="account_id", how="inner"
    )
    baseline_df["reason"] = baseline_df.apply(generate_explanation, axis=1)

    current_df = score_batch()  # reuses the existing scoring logic

    report = compute_drift_report(
        baseline_df=baseline_df,
        current_df=current_df,
        feature_cols=DRIFT_MONITOR_FEATURE_COLS,
        score_col="risk_score",
        baseline_reasons=baseline_df["reason"].tolist(),
        current_reasons=current_df["reason"].tolist(),
    )
    return report


@app.get("/")
def root():
    return {"service": "Fraud Detection ML Service", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict():
    try:
        scored = score_batch()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Required data file missing: {e}")

    flagged = scored[scored["risk_score"] >= 50]
    results = scored[["account_id", "risk_score", "reason", "label"]].to_dict(orient="records")

    return {
        "total_accounts_scored": len(scored),
        "flagged_count": len(flagged),
        "results": results,
    }


@app.get("/drift-report")
def drift_report():
    try:
        report = build_drift_report()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Required data file missing: {e}")

    return {
        "overall_status": report.overall_status,
        "score_psi": report.score_psi,
        "feature_psi": report.feature_psi,
        "explanation_js_divergence": report.explanation_js_divergence,
        "alerts": report.alerts,
        "summary_text": report.summary_text(),
    }