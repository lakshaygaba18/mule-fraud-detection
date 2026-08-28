from fastapi import FastAPI, HTTPException
import pandas as pd
from drift_monitor import compute_drift_report

app = FastAPI(
    title="Fraud Detection ML Service",
    description="Lightweight production API for fraud scoring, network analysis and drift monitoring",
    version="1.0.0",
)

BASELINE_FEATURES_FILE = "account_features.csv"
BASELINE_SCORES_FILE = "account_risk_report.csv"
CURRENT_FEATURES_FILE = "drift_account_features.csv"
CURRENT_SCORES_FILE = "drift_account_risk_report.csv"
TRANSACTIONS_FILE = "drift_transactions.csv"

FEATURE_COLS = [
    "in_degree",
    "out_degree",
    "unique_senders",
    "unique_receivers",
    "pass_through_ratio",
    "velocity_hours",
    "in_span_hours",
]
DRIFT_MONITOR_FEATURE_COLS = FEATURE_COLS + ["is_passthrough"]

HIGH_RISK_THRESHOLD = 50
MAX_NODES = 120


def generate_explanation(row):
    reasons = []

    if row.get("in_degree", 0) >= 5:
        reasons.append(
            f"received money from {row.get('unique_senders', 0)} different senders"
        )

    velocity = row.get("velocity_hours", 999999)
    if pd.notna(velocity) and velocity < 100:
        reasons.append(
            f"forwarded funds onward within {velocity:.1f} hours of receiving them"
        )

    passthrough = row.get("pass_through_ratio", 0)
    if pd.notna(passthrough) and passthrough > 0.7:
        reasons.append(
            f"passed on {passthrough * 100:.0f}% of everything it received"
        )

    span = row.get("in_span_hours", 999999)
    degree = row.get("in_degree", 0)
    if pd.notna(span) and span < 48 and degree >= 3:
        reasons.append(
            f"all incoming payments arrived within a {span:.1f}-hour window"
        )

    avg_in = row.get("avg_in_amount", 0)
    if (
        pd.notna(avg_in)
        and degree <= 1
        and row.get("out_degree", 0) == 0
        and avg_in > 3000
    ):
        reasons.append(
            f"received a single sudden payment of ~₹{avg_in:.0f} "
            "with no prior transaction history and no outbound activity yet"
        )

    return "; ".join(reasons) if reasons else (
        "flagged by the model based on a combination of subtler behavioral signals"
    )


def load_scored_report():
    try:
        scored = pd.read_csv(BASELINE_SCORES_FILE)
        features = pd.read_csv(BASELINE_FEATURES_FILE)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Required data file missing: {e}",
        )

    if "risk_score" not in scored.columns:
        raise HTTPException(
            status_code=500,
            detail=f"{BASELINE_SCORES_FILE} does not contain risk_score",
        )

    if "account_id" not in scored.columns:
        raise HTTPException(
            status_code=500,
            detail=f"{BASELINE_SCORES_FILE} does not contain account_id",
        )

    # Add feature columns if the report only contains account_id/risk_score.
    feature_columns = [
        c for c in features.columns
        if c != "account_id" and c not in scored.columns
    ]
    if feature_columns:
        scored = scored.merge(
            features[["account_id"] + feature_columns],
            on="account_id",
            how="left",
        )

    if "reason" not in scored.columns:
        scored["reason"] = scored.apply(generate_explanation, axis=1)

    if "label" not in scored.columns:
        scored["label"] = 0

    return scored


def load_current_report():
    try:
        features = pd.read_csv(CURRENT_FEATURES_FILE)
        scores = pd.read_csv(CURRENT_SCORES_FILE)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Required drift data file missing: {e}",
        )

    if "risk_score" not in scores.columns:
        raise HTTPException(
            status_code=500,
            detail=f"{CURRENT_SCORES_FILE} does not contain risk_score",
        )

    current = features.merge(
        scores[["account_id", "risk_score"]],
        on="account_id",
        how="inner",
    )

    current["reason"] = current.apply(generate_explanation, axis=1)

    if "label" not in current.columns:
        current["label"] = 0

    return current


@app.get("/")
def root():
    return {
        "service": "Fraud Detection ML Service",
        "status": "running",
        "mode": "production",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict():
    scored = load_scored_report()

    flagged = scored[scored["risk_score"] >= HIGH_RISK_THRESHOLD]

    results = scored[
        ["account_id", "risk_score", "reason", "label"]
    ].to_dict(orient="records")

    return {
        "total_accounts_scored": len(scored),
        "flagged_count": len(flagged),
        "results": results,
    }


@app.get("/network")
def network():
    scored = load_scored_report()

    try:
        tx = pd.read_csv(TRANSACTIONS_FILE)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Required transaction file missing: {e}",
        )

    high_risk_accounts = set(
        scored.loc[
            scored["risk_score"] >= HIGH_RISK_THRESHOLD,
            "account_id",
        ]
    )

    connected_accounts = set(high_risk_accounts)

    for row in tx.itertuples(index=False):
        sender = getattr(row, "sender")
        receiver = getattr(row, "receiver")

        if sender in high_risk_accounts:
            connected_accounts.add(receiver)

        if receiver in high_risk_accounts:
            connected_accounts.add(sender)

    scored_ids = set(scored["account_id"])
    connected_accounts &= scored_ids

    nodes_df = scored[
        scored["account_id"].isin(connected_accounts)
    ].copy()

    if len(nodes_df) > MAX_NODES:
        high_risk_nodes = nodes_df[
            nodes_df["risk_score"] >= HIGH_RISK_THRESHOLD
        ]

        remaining = MAX_NODES - len(high_risk_nodes)

        if remaining > 0:
            neighbors = nodes_df[
                nodes_df["risk_score"] < HIGH_RISK_THRESHOLD
            ].sort_values(
                "risk_score",
                ascending=False,
            ).head(remaining)

            nodes_df = pd.concat([high_risk_nodes, neighbors])
        else:
            nodes_df = high_risk_nodes.head(MAX_NODES)

    selected_ids = set(nodes_df["account_id"])

    nodes = []

    for row in nodes_df.itertuples(index=False):
        risk_score = float(row.risk_score)

        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "UNCERTAIN"
        else:
            risk_level = "LOW"

        label = getattr(row, "label", 0)
        if pd.isna(label):
            label = 0

        nodes.append({
            "id": str(row.account_id),
            "riskScore": risk_score,
            "riskLevel": risk_level,
            "label": int(label),
        })

    edges = []

    has_amount = "amount" in tx.columns

    for row in tx.itertuples(index=False):
        sender = str(getattr(row, "sender"))
        receiver = str(getattr(row, "receiver"))

        if sender not in selected_ids or receiver not in selected_ids:
            continue

        amount = 0.0
        if has_amount:
            value = getattr(row, "amount")
            if pd.notna(value):
                amount = float(value)

        edges.append({
            "source": sender,
            "target": receiver,
            "amount": amount,
        })

    return {
        "nodeCount": len(nodes),
        "edgeCount": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


@app.get("/drift-report")
def drift_report():
    baseline = load_scored_report()
    current = load_current_report()

    try:
        report = compute_drift_report(
            baseline_df=baseline,
            current_df=current,
            feature_cols=DRIFT_MONITOR_FEATURE_COLS,
            score_col="risk_score",
            baseline_reasons=baseline["reason"].tolist(),
            current_reasons=current["reason"].tolist(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not compute drift report: {e}",
        )

    return {
        "overall_status": report.overall_status,
        "score_psi": report.score_psi,
        "feature_psi": report.feature_psi,
        "explanation_js_divergence": report.explanation_js_divergence,
        "alerts": report.alerts,
        "summary_text": report.summary_text(),
    }
