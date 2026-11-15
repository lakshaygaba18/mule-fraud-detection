
import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp_server import data

MULE = "MULE_07aaf84e"
HIDDEN_KEYS = {"label", "sender_label", "receiver_label"}


def all_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from all_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from all_keys(item)


def test_risk_level_bands():
    assert data.risk_level(100) == "HIGH"
    assert data.risk_level(70) == "HIGH"
    assert data.risk_level(69.9) == "UNCERTAIN"
    assert data.risk_level(40) == "UNCERTAIN"
    assert data.risk_level(39.9) == "LOW"


def test_unknown_account_returns_error_not_crash():
    for fn in (
        data.get_account,
        data.investigate_account,
        data.get_network_graph,
    ):
        assert "error" in fn("DOES_NOT_EXIST")

    assert "error" in data.trace_transactions("DOES_NOT_EXIST")


def test_trace_rejects_bad_direction():
    assert "error" in data.trace_transactions(
        MULE, direction="sideways"
    )


def test_known_mule_summary():
    acc = data.get_account(MULE)
    assert acc["risk_level"] == "HIGH"
    assert acc["unique_senders"] == 13
    assert acc["is_single_in_single_out_relay"] is False


def test_no_ground_truth_labels_leak():
    outputs = [
        data.list_flagged_accounts(5),
        data.investigate_account(MULE),
        data.trace_transactions(MULE, "both", 2),
        data.get_network_graph(MULE, 1),
        data.get_drift_report(),
    ]

    for out in outputs:
        assert not (HIDDEN_KEYS & set(all_keys(out)))


def test_placeholder_hours_never_exposed():
    for acc_id in list(data._risk.index[:300]):
        acc = data.get_account(acc_id)

        for key in ("velocity_hours", "in_span_hours"):
            assert acc[key] is None or acc[key] < 999999


def test_trace_total_matches_account_outflow():
    checked = 0

    for acc_id in data._risk.index[:200]:
        acc = data.get_account(acc_id)

        if acc["total_out"] > 0:
            trace = data.trace_transactions(
                acc_id, "out", 1, max_edges=1000
            )
            assert trace["total_amount"] == pytest.approx(
                acc["total_out"], abs=0.05
            )
            checked += 1

    assert checked > 0


def test_network_graph_is_consistent():
    g = data.get_network_graph(MULE, radius=1, max_nodes=20)
    ids = {n["id"] for n in g["nodes"]}

    assert MULE in ids
    assert len(ids) <= 20

    for e in g["edges"]:
        assert e["from"] in ids
        assert e["to"] in ids

    assert g["summary"]["nodes_returned"] == len(ids)


def test_investigation_contains_evidence_and_caveats():
    r = data.investigate_account(MULE)

    assert r["evidence"]
    assert "simulated" in r["reliability"]["data_source"]
    assert r["caveats"]


def test_drift_report_has_limitations():
    d = data.get_drift_report()

    assert "error" in d or (
        "overall_status" in d and d["limitations"]
    )


def test_mcp_server_exposes_expected_tools():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(ROOT / "mcp_server" / "server.py")],
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return {t.name for t in tools.tools}

    assert asyncio.run(run()) == {
        "list_flagged_accounts",
        "investigate_account",
        "trace_transactions",
        "get_network_graph",
        "get_drift_report",
    }
