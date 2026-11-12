from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

_risk = pd.read_csv(ROOT / "account_risk_report.csv").set_index("account_id")
_feats = pd.read_csv(ROOT / "account_features.csv").set_index("account_id")
_txns = pd.read_csv(ROOT / "transactions.csv", parse_dates=["timestamp"])

# Simulator ground truth: never expose these to the agent
_HIDDEN = {"label", "sender_label", "receiver_label"}


def risk_level(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "UNCERTAIN"
    return "LOW"


def _clean_hours(v):
    v = float(v)
    return None if v >= 999999 else round(v, 1)


def get_account(account_id: str) -> dict:
    if account_id not in _risk.index:
        return {"error": f"Unknown account_id: {account_id}"}
    row = _risk.loc[account_id]
    score = float(row["risk_score"])
    return {
        "account_id": account_id,
        "risk_score": round(score, 1),
        "risk_level": risk_level(score),
        "in_degree": int(row["in_degree"]),
        "out_degree": int(row["out_degree"]),
        "unique_senders": int(row["unique_senders"]),
        "unique_receivers": int(row["unique_receivers"]),
        "total_in": round(float(row["total_in"]), 2),
        "total_out": round(float(row["total_out"]), 2),
        "pass_through_pct": round(min(float(row["pass_through_ratio"]), 1.0) * 100, 1),
        "velocity_hours": _clean_hours(row["velocity_hours"]),
        "in_span_hours": _clean_hours(row["in_span_hours"]),
        "is_passthrough": bool(_feats.loc[account_id, "is_passthrough"]),
    }


_by_sender = {k: g for k, g in _txns.groupby("sender")}
_by_receiver = {k: g for k, g in _txns.groupby("receiver")}


def _level(acc: str) -> str:
    if acc in _risk.index:
        return risk_level(float(_risk.loc[acc, "risk_score"]))
    return "UNKNOWN"


def trace_transactions(account_id: str, direction: str = "out",
                       depth: int = 2, max_edges: int = 40) -> dict:
    if account_id not in _risk.index:
        return {"error": f"Unknown account_id: {account_id}"}
    if direction not in ("out", "in", "both"):
        return {"error": "direction must be 'out', 'in' or 'both'"}
    depth = max(1, min(int(depth), 4))

    seen = {account_id}
    seen_txn = set()
    frontier = [account_id]
    edges = []

    for hop in range(1, depth + 1):
        nxt = []
        for acc in frontier:
            frames = []
            if direction in ("out", "both") and acc in _by_sender:
                frames.append(("out", _by_sender[acc]))
            if direction in ("in", "both") and acc in _by_receiver:
                frames.append(("in", _by_receiver[acc]))
            for d, g in frames:
                for r in g.itertuples():
                    if r.txn_id in seen_txn:
                        continue
                    seen_txn.add(r.txn_id)
                    other = r.receiver if d == "out" else r.sender
                    edges.append({
                        "hop": hop,
                        "from": r.sender,
                        "to": r.receiver,
                        "amount": round(float(r.amount), 2),
                        "timestamp": r.timestamp.isoformat(),
                        "counterparty": other,
                        "counterparty_risk": _level(other),
                    })
                    if other not in seen:
                        seen.add(other)
                        nxt.append(other)
        frontier = nxt
        if not frontier:
            break

    reached = seen - {account_id}
    high_risk = sorted(a for a in reached if _level(a) == "HIGH")
    top = sorted(edges, key=lambda e: e["amount"], reverse=True)[:max_edges]
    return {
        "account_id": account_id,
        "direction": direction,
        "depth": depth,
        "transactions_found": len(edges),
        "total_amount": round(sum(e["amount"] for e in edges), 2),
        "accounts_reached": len(reached),
        "high_risk_accounts_reached": high_risk[:15],
        "top_transactions_by_amount": top,
        "truncated": len(edges) > max_edges,
    }


def investigate_account(account_id: str) -> dict:
    acc = get_account(account_id)
    if "error" in acc:
        return acc
    inc = _by_receiver.get(account_id)
    out = _by_sender.get(account_id)
    evidence = []

    if inc is not None:
        n, s = len(inc), inc["sender"].nunique()
        msg = (f"Received {n} payment{'s' if n != 1 else ''} totalling "
               f"{inc['amount'].sum():,.2f} from {s} distinct sender{'s' if s != 1 else ''}")
        if n > 1:
            span = (inc["timestamp"].max() - inc["timestamp"].min()).total_seconds() / 3600
            msg += f" within {span:.1f} hours"
        evidence.append(msg + ".")
        high_in = inc[inc["sender"].map(_level) == "HIGH"]
        if len(high_in) > 0:
            evidence.append(
                f"{high_in['amount'].sum() / inc['amount'].sum():.0%} of incoming money "
                f"({high_in['amount'].sum():,.2f}) came from {high_in['sender'].nunique()} HIGH-risk account(s)."
            )
    if inc is not None and out is not None:
        gap = (out["timestamp"].min() - inc["timestamp"].max()).total_seconds() / 3600
        if gap >= 0:
            evidence.append(
                f"The first outgoing payment came {gap:.1f} hours after the last incoming one."
            )
        else:
            evidence.append(
                "Outgoing payments started before incoming payments finished (overlapping activity)."
            )
    if out is not None:
        total_out = out["amount"].sum()
        levels = out["receiver"].map(_level)
        high = out[levels == "HIGH"]
        if len(high) > 0:
            evidence.append(
                f"{high['amount'].sum() / total_out:.0%} of outgoing money "
                f"({high['amount'].sum():,.2f}) went to {high['receiver'].nunique()} HIGH-risk account(s)."
            )
    if acc["total_in"] > 0 and acc["total_out"] > 0:
        evidence.append(
            f"Total outflow was {acc['total_out'] / acc['total_in']:.2f}x the total inflow."
        )

    return {
        "account": acc,
        "evidence": evidence,
        "data_source": "simulated transactions, not real bank data",
        "caveats": [
            "The risk score comes from a model trained on simulated data.",
            "A high score is a signal for human review, not proof of fraud.",
        ],
    }

def list_flagged_accounts(limit: int = 10, min_score: float = 70.0) -> dict:
    limit = max(1, min(int(limit), 50))
    df = _risk[_risk["risk_score"] >= min_score].sort_values("risk_score", ascending=False)
    return {
        "total_matching": int(len(df)),
        "accounts": [
            {"account_id": a, "risk_score": round(float(s), 1), "risk_level": risk_level(float(s))}
            for a, s in df["risk_score"].head(limit).items()
        ],
    }