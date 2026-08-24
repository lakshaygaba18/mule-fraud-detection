"""
simulate_drift_batch.py

Generates a NEW batch of transactions that mimics "next month's traffic":
- same normal-account behavior as before (so most of the data looks familiar)
- the same old mule-ring pattern, but FEWER of them (fraud tactics shift)
- a brand-new pattern: "structuring" mule accounts, which spread money
  across many small, slow, innocent-looking transfers instead of the
  fast pile-up-then-cash-out pattern your model was trained on.

This is the "fraud tactics evolve" scenario: the labels below are still
generated (so YOU can check recall on the new pattern), but in a real
deployment you would NOT have these labels yet -- which is exactly why
drift_monitor.py detecting a distribution shift, without needing labels,
matters.

Output: drift_transactions.csv (same schema as transactions.csv)
"""
import random
import uuid
import csv
from datetime import datetime, timedelta

random.seed(99)  # different seed -> genuinely new random traffic, not a replay

# ---------------- CONFIG ----------------
NUM_NORMAL_ACCOUNTS = 1200
NUM_OLD_STYLE_MULE_RINGS = 15   # old pattern still appears, just less often
NUM_STRUCTURING_RINGS = 25      # NEW pattern -- this is the drift
SENDERS_PER_RING = (5, 20)
CASHOUT_PER_RING = (1, 4)
SIM_DAYS = 30
OUTPUT_FILE = "drift_transactions.csv"
# -----------------------------------------

start_date = datetime(2026, 2, 1)  # "next month"


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


def simulate_old_style_mule_ring():
    """Same fast pile-up-then-cash-out pattern as the original training data."""
    mule = new_account_id("MULE")
    num_senders = random.randint(*SENDERS_PER_RING)
    num_cashout = random.randint(*CASHOUT_PER_RING)
    senders = [new_account_id("SRC") for _ in range(num_senders)]
    cashouts = [new_account_id("OUT") for _ in range(num_cashout)]

    ring_start = random_timestamp(day_offset_range=(0, SIM_DAYS - 2))
    transactions = []
    total_in = 0.0

    for s in senders:
        amount = round(random.uniform(500, 50000), 2)
        ts = ring_start + timedelta(hours=random.uniform(0, 36))
        transactions.append({
            "txn_id": uuid.uuid4().hex, "sender": s, "receiver": mule,
            "amount": amount, "timestamp": ts.isoformat(),
        })
        total_in += amount

    remaining = total_in
    for i, c in enumerate(cashouts):
        share = remaining / (len(cashouts) - i) if i < len(cashouts) - 1 else remaining
        share = round(share * random.uniform(0.8, 0.95), 2)
        last_inbound_ts = max(datetime.fromisoformat(t["timestamp"]) for t in transactions)
        ts = last_inbound_ts + timedelta(minutes=random.uniform(2, 45))
        transactions.append({
            "txn_id": uuid.uuid4().hex, "sender": mule, "receiver": c,
            "amount": share, "timestamp": ts.isoformat(),
        })
        remaining -= share

    ring_accounts = [mule] + senders + cashouts
    labels = {mule: 1}
    for c in cashouts:
        labels[c] = 1
    for s in senders:
        labels[s] = 0
    return ring_accounts, labels, transactions


def simulate_structuring_ring():
    """
    NEW fraud pattern: instead of one mule account piling up money fast and
    cashing out immediately, the money is split across MANY small transfers,
    spread over days (not hours), each individually looking like normal
    person-to-person activity. This deliberately avoids the exact signals
    your current features/model were trained to catch:
      - in_degree stays LOW per hop (money moves through a longer chain)
      - velocity_hours is HIGH (slow, patient movement, not a fast cash-out)
      - amounts are small and "normal-looking", not one big lump sum
    """
    num_hops = random.randint(4, 7)  # money passes through a longer chain
    chain = [new_account_id("STRUCT") for _ in range(num_hops)]
    source_senders = [new_account_id("SRC") for _ in range(random.randint(6, 15))]
    final_cashout = new_account_id("OUT")

    transactions = []
    ring_start = random_timestamp(day_offset_range=(0, SIM_DAYS - 10))

    # many small amounts flow into the first hop from many senders, spread
    # across several days -- NOT a single sudden pile-up
    total_in = 0.0
    for s in source_senders:
        amount = round(random.uniform(400, 9000), 2)  # small, below-radar amounts
        ts = ring_start + timedelta(days=random.uniform(0, 5))
        transactions.append({
            "txn_id": uuid.uuid4().hex, "sender": s, "receiver": chain[0],
            "amount": amount, "timestamp": ts.isoformat(),
        })
        total_in += amount

    # money slowly walks down the chain, one hop at a time, with real delays
    remaining = total_in
    current_ts = max(datetime.fromisoformat(t["timestamp"]) for t in transactions)
    for i in range(len(chain) - 1):
        share = round(remaining * random.uniform(0.85, 0.97), 2)
        current_ts = current_ts + timedelta(hours=random.uniform(12, 60))  # slow!
        transactions.append({
            "txn_id": uuid.uuid4().hex, "sender": chain[i], "receiver": chain[i + 1],
            "amount": share, "timestamp": current_ts.isoformat(),
        })
        remaining = share

    # final hop cashes out
    current_ts = current_ts + timedelta(hours=random.uniform(12, 60))
    transactions.append({
        "txn_id": uuid.uuid4().hex, "sender": chain[-1], "receiver": final_cashout,
        "amount": round(remaining, 2), "timestamp": current_ts.isoformat(),
    })

    ring_accounts = chain + source_senders + [final_cashout]
    labels = {acc: 1 for acc in chain}
    labels[final_cashout] = 1
    for s in source_senders:
        labels[s] = 0
    return ring_accounts, labels, transactions


def main():
    accounts, transactions = simulate_normal_accounts(NUM_NORMAL_ACCOUNTS)
    all_labels = {}

    for _ in range(NUM_OLD_STYLE_MULE_RINGS):
        ring_accounts, labels, ring_tx = simulate_old_style_mule_ring()
        accounts.extend(ring_accounts)
        transactions.extend(ring_tx)
        all_labels.update(labels)

    for _ in range(NUM_STRUCTURING_RINGS):
        ring_accounts, labels, ring_tx = simulate_structuring_ring()
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
    print(f"  - old-style mule rings: {NUM_OLD_STYLE_MULE_RINGS}")
    print(f"  - NEW structuring rings: {NUM_STRUCTURING_RINGS}  <-- this is the drift")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()