import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP
from mcp_server import data

mcp = FastMCP("muleshield")


@mcp.tool()
def list_flagged_accounts(limit: int = 10, min_score: float = 70.0) -> dict:
    """List the highest-risk accounts, sorted by model risk score (0-100).
    Use this first when the user has not named a specific account."""
    return data.list_flagged_accounts(limit, min_score)


@mcp.tool()
def investigate_account(account_id: str) -> dict:
    """Investigate one account for possible mule activity. Returns the model's
    risk score and level, behavioural statistics, evidence computed from the
    raw transactions, and caveats. A high score is a signal for human review,
    not proof of fraud. Account ID prefixes (MULE_, OUT_, SRC_) come from the
    simulator and must NOT be treated as evidence."""
    return data.investigate_account(account_id)


@mcp.tool()
def trace_transactions(account_id: str, direction: str = "out", depth: int = 2) -> dict:
    """Trace money flows from an account. direction is 'out' (where money went),
    'in' (where it came from) or 'both'. depth is the number of hops (1-4).
    Each transaction includes amount, timestamp and the counterparty's risk level."""
    return data.trace_transactions(account_id, direction, depth)


if __name__ == "__main__":
    mcp.run()