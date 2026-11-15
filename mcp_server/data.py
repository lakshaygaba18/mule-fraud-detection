import contextlib
import functools
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

_risk = pd.read_csv(ROOT / "account_risk_report.csv").set_index("account_id")
_feats = pd.read_csv(ROOT / "account_features.csv").set_index("account_id")
_txns = pd.read_csv(ROOT / "transactions.csv", parse_dates=["timestamp"])

# Simulator ground truth: never expose these to the agent
_HIDDEN = {"label", "sender_label", "receiver_label"}

DRIFT_FEATURE_COLS = [
    "in_degree", "out_degree", "unique_senders", "unique_receivers",
    "pass_through_ratio", "velocity_hours", "in_span_hours", "is_passthrough",
]


def risk_level(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "UNCERTAIN"
    return "LOW"


def _clean_hours(v):
    v = float(v)
    return None if v >= 999999 else round(v, 1)


def _score(acc: str) -> float:
    return float(_risk.loc[acc, "risk_score"]) if acc in _risk.index else -1.0


def _level(acc: str) -> str:
    if acc in _risk.index:
        return risk_level(_score(acc))
    return "UNKNOWN"


_by_sender = {k: g for k, g in _txns.groupby("sender")}
_by_receiver = {k: g for k, g in _txns.groupby("receiver")}


# ---------------------------------------------------------------- drift

def _plain(obj):
    return json.loads(json.dumps(
        obj, default=lambda o: float(o) if hasattr(o, "__float__") else str(o)))


def _with_passthrough(risk_df: pd.DataFrame, feats_df: pd.DataFrame) -> pd.DataFrame:
    if "is_passthrough" in risk_df.columns:
        return risk_df
    return risk_df.merge(feats_df[["account_id", "is_passthrough"]], on="account_id", how="left")


@functools.lru_cache(maxsize=1)
def _drift_cached() -> str:
    cur_risk_path = ROOT / "drift_account_risk_report.csv"
    cur_feat_path = ROOT / "drift_account_features.csv"
    if not cur_risk_path.exists() or not cur_feat_path.exists():
        return json.dumps({"error": "Drift comparison files (drift_account_*.csv) were not found in the project folder."})
    try:
        # drift_monitor may print at import time; stdout is the MCP channel, so send it to stderr
        with contextlib.redirect_stdout(sys.stderr):
            from drift_monitor import compute_drift_report
            base = _with_passthrough(_risk.reset_index(), _feats.reset_index())
            cur = _with_passthrough(pd.read_csv(cur_risk_path), pd.read_csv(cur_feat_path))
            report = compute_drift_report(
                baseline_df=base,
                current_df=cur,
                feature_cols=DRIFT_FEATURE_COLS,
                score_col="risk_score",
            )
            summary = report.summary_text()
        worst = max(report.feature_psi.items(), key=lambda kv: kv[1], default=(None, 0.0))
        return json.dumps(_plain({
            "overall_status": report.overall_status,
            "score_psi": report.score_psi,
            "feature_psi": report.feature_psi,
            "most_drifted_feature": {"name": worst[0], "psi": worst[1]},
            "alerts": report.alerts,
            "summary_text": summary,
            "baseline_accounts": int(len(base)),
            "current_accounts": int(len(cur)),
            "limitations": [
                "Compares two simulated batches of accounts, not live production traffic.",
                "Input-feature PSI cannot detect a change in the relationship between features and fraud. "
                "On the real Elliptic dataset, feature-level PSI did not warn before the model collapsed.",
                "Explanation-pattern drift is not computed here.",
            ],
        }))
    except Exception as e:
        return json.dumps({"error": f"Could not compute drift report: {e}"})


def get_drift_report() -> dict:
    return json.loads(_drift_cached())


def _drift_headline() -> str:
    d = get_drift_report()
    if "error" in d:
        return "unavailable: " + d["error"]
    return f"{d['overall_status']} (score PSI {d['score_psi']:.3f}); call get_drift_report for details"


# ---------------------------------------------------------------- tools

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
        # True only for the strict chain-relay pattern: exactly 1 sender AND 1 receiver.
        # False does NOT mean the account is not a mule.
        "is_single_in_single_out_relay": bool(_feats.loc[account_id, "is_passthrough"]),
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


def get_network_graph(account_id: str, radius: int = 1, max_nodes: int = 30) -> dict:
    if account_id not in _risk.index:
        return {"error": f"Unknown account_id: {account_id}"}
    radius = max(1, min(int(radius), 2))
    max_nodes = max(5, min(int(max_nodes), 60))

    nodes = {account_id}
    frontier = {account_id}
    for _ in range(radius):
        nxt = set()
        for acc in frontier:
            if acc in _by_sender:
                nxt.update(_by_sender[acc]["receiver"])
            if acc in _by_receiver:
                nxt.update(_by_receiver[acc]["sender"])
        frontier = nxt - nodes
        nodes |= frontier

    total_nodes = len(nodes)
    if total_nodes > max_nodes:
        others = sorted(nodes - {account_id}, key=lambda a: (-_score(a), a))
        nodes = {account_id, *others[: max_nodes - 1]}

    sub = _txns[_txns["sender"].isin(nodes) & _txns["receiver"].isin(nodes)]
    agg = (
        sub.groupby(["sender", "receiver"])
        .agg(total_amount=("amount", "sum"), payments=("amount", "size"),
             first=("timestamp", "min"), last=("timestamp", "max"))
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    edges_total = len(agg)
    edge_list = [
        {
            "from": r.sender,
            "to": r.receiver,
            "total_amount": round(float(r.total_amount), 2),
            "payments": int(r.payments),
            "first_payment": r.first.isoformat(),
            "last_payment": r.last.isoformat(),
        }
        for r in agg.head(80).itertuples()
    ]
    node_list = [
        {
            "id": a,
            "risk_score": round(_score(a), 1) if a in _risk.index else None,
            "risk_level": _level(a),
            "is_center": a == account_id,
        }
        for a in sorted(nodes, key=lambda a: (a != account_id, -_score(a), a))
    ]
    return {
        "center": account_id,
        "radius": radius,
        "nodes": node_list,
        "edges": edge_list,
        "summary": {
            "nodes_returned": len(node_list),
            "nodes_before_cap": total_nodes,
            "edges_returned": len(edge_list),
            "edges_before_cap": edges_total,
            "high_risk_nodes": sum(1 for n in node_list if n["risk_level"] == "HIGH"),
            "truncated": total_nodes > max_nodes or edges_total > 80,
        },
        "note": ("Edges aggregate all payments between a pair of accounts. "
                 "Only transactions between the returned accounts are shown."),
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
    if acc["is_single_in_single_out_relay"]:
        evidence.append("Exactly one sender and one receiver (single-in, single-out relay pattern).")

    return {
        "account": acc,
        "evidence": evidence,
        "reliability": {
            "data_source": "simulated transactions, not real bank data",
            "score_type": "model prediction, not a verified fraud finding",
            "score_distribution_note": ("On this simulated data most scores sit near 0 or near 100, "
                                        "so a score does not express graded confidence."),
            "relay_flag_note": ("is_single_in_single_out_relay only detects accounts with exactly one "
                                "sender and one receiver. False does not mean the account is not a mule."),
            "drift_status": _drift_headline(),
        },
        "caveats": [
            "The risk score comes from a model trained on simulated data.",
            "A high score is a signal for human review, not proof of fraud.",
        ],
    }