import pandas as pd

RISK_REPORT_FILE = "account_risk_report.csv"
TRANSACTIONS_FILE = "transactions.csv"
OUTPUT_FILE = "account_risk_report_propagated.csv"

HIGH_RISK_THRESHOLD = 70.0
BOOST_FACTOR = 0.25
MAX_BOOST = 20.0


def build_neighbor_map(tx: pd.DataFrame) -> dict:
    neighbors = {}
    for _, row in tx.iterrows():
        s, r = row["sender"], row["receiver"]
        neighbors.setdefault(s, set()).add(r)
        neighbors.setdefault(r, set()).add(s)
    return neighbors


def propagate(risk_df: pd.DataFrame, neighbor_map: dict) -> pd.DataFrame:
    risk_lookup = dict(zip(risk_df["account_id"], risk_df["risk_score"]))

    propagated_scores = []
    reasons = []

    for _, row in risk_df.iterrows():
        account_id = row["account_id"]
        base_score = row["risk_score"]

        neighbors = neighbor_map.get(account_id, set())
        high_risk_neighbors = [
            (n, risk_lookup[n]) for n in neighbors
            if n in risk_lookup and risk_lookup[n] >= HIGH_RISK_THRESHOLD
        ]

        if high_risk_neighbors:
            worst_neighbor_id, worst_neighbor_score = max(
                high_risk_neighbors, key=lambda x: x[1]
            )
            boost = min(worst_neighbor_score * BOOST_FACTOR, MAX_BOOST)
            new_score = min(base_score + boost, 100.0)

            propagated_scores.append(round(new_score, 1))
            reasons.append(
                f"+{boost:.1f} risk propagated from directly connected "
                f"high-risk account {worst_neighbor_id} (risk {worst_neighbor_score:.1f})"
            )
        else:
            propagated_scores.append(base_score)
            reasons.append("")

    risk_df = risk_df.copy()
    risk_df["propagated_risk_score"] = propagated_scores
    risk_df["propagation_reason"] = reasons
    return risk_df


def main():
    risk_df = pd.read_csv(RISK_REPORT_FILE)
    tx = pd.read_csv(TRANSACTIONS_FILE)

    neighbor_map = build_neighbor_map(tx)
    result = propagate(risk_df, neighbor_map)

    n_boosted = (result["propagation_reason"] != "").sum()
    print(f"Accounts scored: {len(result)}")
    print(f"Accounts boosted by risk propagation: {n_boosted}")

    if n_boosted > 0:
        print("\nSample boosted accounts:")
        sample = result[result["propagation_reason"] != ""].head(5)
        for _, row in sample.iterrows():
            print(f"  {row['account_id']}: {row['risk_score']:.1f} -> {row['propagated_risk_score']:.1f}")
            print(f"    {row['propagation_reason']}")

    result.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()