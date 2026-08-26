"""
simulate_adversarial_batch.py

ROBUSTNESS TEST: designs a fraud pattern that specifically tries to evade
BOTH detectors you've built so far:
  1. The GNN/score-based detector (trained on in_degree, velocity_hours, etc.)
  2. The is_passthrough topology monitor (which flagged in_degree==1 AND
     out_degree==1 as suspicious)

"Adversarial braiding" pattern: instead of a clean 1-in-1-out chain, each
hop splits its incoming money into TWO outbound transfers to two different
next-hop accounts (which later recombine before cash-out). This gives every
middle-of-chain account out_degree=2, defeating is_passthrough by
construction, while still moving money through a long, slow, low-profile
chain like the original structuring pattern.

This is a genuine "red-team your own system" exercise -- the output tells
you whether your monitoring generalizes to genuinely unseen evasion, or was
overfit to the exact pattern you tested it on.
"""
import random
import uuid
import csv
from datetime import datetime, timedelta

random.seed(7)

NUM_NORMAL_ACCOUNTS = 1200
NUM_ADVERSARIAL_RINGS = 25
SIM_DAYS = 30
OUTPUT_FILE = "adversarial_transactions.csv"

start_date = datetime(2026, 3, 1)  # "month after that"


def random_timestamp(day_offset_range=(0, SIM_DAYS)):
    day = random.uniform(*day_offset_range)
    return start_date + timedelta(days=day)


def new_account_id(prefix="ACC"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def simulate_normal_accounts(n, business_fraction=0.12):
    accounts = [new_account_id() for _ in range(n)]
    is_business = {acc: (random.random() < business_fraction) for acc in accounts}
    transactions = []

    for acc in accounts:
        num_counterparties = random.randint(2, 6)
        counterparties = random.sample(accounts, min(num_counterparties, len(accounts) - 1))
        num_txns = random.randint(3, 15)

        for _ in range(num_txns):
            receiver = random.choice(counterparties)
            if receiver == acc:
                continue
            if is_business.get(receiver, False):
                amount = round(random.uniform(3000, 60000), 2)
            elif random.random() < 0.08:
                amount = round(random.uniform(3000, 60000), 2)
            else:
                amount = round(random.lognormvariate(6.5, 1.0), 2)

            ts = random_timestamp()
            transactions.append({
                "txn_id": uuid.uuid4().hex, "sender": acc, "receiver": receiver,
                "amount": amount, "timestamp": ts.isoformat(),
            })
    return accounts, transactions


def simulate_adversarial_ring():
    """
    Braided chain: source senders -> hop1 (splits into 2) -> hop2a, hop2b
    (each splits into 2 again, but recombine some flow) -> final cash-out.
    Every middle account has out_degree=2, evading is_passthrough by design.
    """
    num_layers = random.randint(2, 3)
    source_senders = [new_account_id("SRC") for _ in range(random.randint(6, 15))]
    final_cashout = new_account_id("OUT")

    transactions = []
    ring_start = random_timestamp(day_offset_range=(0, SIM_DAYS - 10))

    # layer 0: many small senders -> first hop account
    hop_start = new_account_id("BRAID")
    total_in = 0.0
    for s in source_senders:
        amount = round(random.uniform(400, 9000), 2)
        ts = ring_start + timedelta(days=random.uniform(0, 5))
        transactions.append({
            "txn_id": uuid.uuid4().hex, "sender": s, "receiver": hop_start,
            "amount": amount, "timestamp": ts.isoformat(),
        })
        total_in += amount

    current_layer = [hop_start]
    current_amounts = [total_in]
    current_ts = max(datetime.fromisoformat(t["timestamp"]) for t in transactions)

    for layer in range(num_layers):
        next_layer = []
        next_amounts = []
        for acc, amt in zip(current_layer, current_amounts):
            # split into 2 outbound transfers -- defeats out_degree==1 check
            a1 = new_account_id("BRAID")
            a2 = new_account_id("BRAID")
            share1 = round(amt * random.uniform(0.45, 0.55), 2)
            share2 = round(amt - share1, 2)

            current_ts = current_ts + timedelta(hours=random.uniform(12, 48))
            transactions.append({
                "txn_id": uuid.uuid4().hex, "sender": acc, "receiver": a1,
                "amount": share1, "timestamp": current_ts.isoformat(),
            })
            transactions.append({
                "txn_id": uuid.uuid4().hex, "sender": acc, "receiver": a2,
                "amount": share2, "timestamp": current_ts.isoformat(),
            })
            next_layer.extend([a1, a2])
            next_amounts.extend([share1, share2])

        current_layer, current_amounts = next_layer, next_amounts

    # final layer: all braided accounts cash out to the same final account
    for acc, amt in zip(current_layer, current_amounts):
        current_ts = current_ts + timedelta(hours=random.uniform(6, 24))
        transactions.append({
            "txn_id": uuid.uuid4().hex, "sender": acc, "receiver": final_cashout,
            "amount": amt, "timestamp": current_ts.isoformat(),
        })

    all_braid_accounts = [hop_start] + [
        t["receiver"] for t in transactions
        if t["receiver"].startswith("BRAID_") or t["sender"].startswith("BRAID_")
    ]
    all_braid_accounts = list(set(all_braid_accounts))

    ring_accounts = all_braid_accounts + source_senders + [final_cashout]
    labels = {acc: 1 for acc in all_braid_accounts}
    labels[final_cashout] = 1
    for s in source_senders:
        labels[s] = 0
    return ring_accounts, labels, transactions


def main():
    accounts, transactions = simulate_normal_accounts(NUM_NORMAL_ACCOUNTS)
    all_labels = {}

    for _ in range(NUM_ADVERSARIAL_RINGS):
        ring_accounts, labels, ring_tx = simulate_adversarial_ring()
        accounts.extend(ring_accounts)
        transactions.extend(ring_tx)
        all_labels.update(labels)

    for acc in accounts:
        if acc not in all_labels:
            all_labels[acc] = 0

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "txn_id", "sender", "receiver", "amount", "timestamp",
            "sender_label", "receiver_label"
        ])
        writer.writeheader()
        for txn in transactions:
            txn["sender_label"] = all_labels.get(txn["sender"], 0)
            txn["receiver_label"] = all_labels.get(txn["receiver"], 0)
            writer.writerow(txn)

    n_fraud_accounts = sum(1 for v in all_labels.values() if v == 1)
    print(f"Generated {len(transactions)} transactions")
    print(f"Generated {len(accounts)} accounts ({n_fraud_accounts} labeled fraud/mule)")
    print(f"  - adversarial braided rings: {NUM_ADVERSARIAL_RINGS} "
          f"(each account out_degree=2, designed to evade is_passthrough)")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()