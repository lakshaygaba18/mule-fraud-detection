import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.preprocessing import StandardScaler
from train_gnn import GraphSAGE, build_graph, FEATURE_COLS

FEATURES_FILE = "account_features.csv"
MODEL_FILE = "gnn_model.pt"
TOP_N_TO_EXPLAIN = 10


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


def main():
    data, account_ids = build_graph()

    model = GraphSAGE(in_channels=data.x.shape[1])
    model.load_state_dict(torch.load(MODEL_FILE))
    model.eval()

    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)[:, 1].numpy()

    features = pd.read_csv(FEATURES_FILE)
    features["risk_score"] = (probs * 100).round(1)

    flagged = features.sort_values("risk_score", ascending=False).head(TOP_N_TO_EXPLAIN)

    print(f"=== Top {TOP_N_TO_EXPLAIN} highest-risk accounts, with explanations ===\n")
    for _, row in flagged.iterrows():
        explanation = generate_explanation(row)
        actual = "MULE/FRAUD" if row["label"] == 1 else "actually normal (false positive)"
        print(f"ACCOUNT: {row['account_id']}")
        print(f"RISK SCORE: {row['risk_score']}/100")
        print(f"WHY: {explanation}")
        print(f"GROUND TRUTH: {actual}")
        print("-" * 60)

    features.to_csv("account_risk_report.csv", index=False)
    print("\nFull risk report saved to account_risk_report.csv")


if __name__ == "__main__":
    main()