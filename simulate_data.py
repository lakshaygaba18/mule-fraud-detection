import random
import uuid
import csv
from datetime import datetime, timedelta

random.seed(42)

# ---------------- CONFIG ----------------
NUM_NORMAL_ACCOUNTS = 2000
NUM_MULE_RINGS = 40
SENDERS_PER_RING = (5, 20)
CASHOUT_PER_RING = (1, 4)
SIM_DAYS = 30
OUTPUT_DIR = "data"
OUTPUT_FILE = "transactions.csv"
# -----------------------------------------

start_date = datetime(2026, 1, 1)

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
                "txn_id": uuid.uuid4().hex,
                "sender": acc,
                "receiver": receiver,
                "amount": amount,
                "timestamp": ts.isoformat(),
            })

    return accounts, transactions

def simulate_mule_ring():
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
            "txn_id": uuid.uuid4().hex,
            "sender": s,
            "receiver": mule,
            "amount": amount,
            "timestamp": ts.isoformat(),
        })
        total_in += amount

    remaining = total_in
    for i, c in enumerate(cashouts):
        share = remaining / (len(cashouts) - i) if i < len(cashouts) - 1 else remaining
        share = round(share * random.uniform(0.8, 0.95), 2)
        last_inbound_ts = max(datetime.fromisoformat(t["timestamp"]) for t in transactions)
        ts = last_inbound_ts + timedelta(minutes=random.uniform(2, 45))
        transactions.append({
            "txn_id": uuid.uuid4().hex,
            "sender": mule,
            "receiver": c,
            "amount": share,
            "timestamp": ts.isoformat(),
        })
        remaining -= share

    ring_accounts = [mule] + senders + cashouts
    labels = {mule: 1}
    for c in cashouts:
        labels[c] = 1
    for s in senders:
        labels[s] = 0

    return ring_accounts, labels, transactions

def main():
    accounts, transactions = simulate_normal_accounts(NUM_NORMAL_ACCOUNTS)

    all_labels = {}

    for _ in range(NUM_MULE_RINGS):
        ring_accounts, labels, ring_transactions = simulate_mule_ring()

        accounts.extend(ring_accounts)
        transactions.extend(ring_transactions)
        all_labels.update(labels)

    for acc in accounts:
        if acc not in all_labels:
            all_labels[acc] = 0

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "txn_id",
                "sender",
                "receiver",
                "amount",
                "timestamp",
                "sender_label",
                "receiver_label"
            ]
        )

        writer.writeheader()

        for txn in transactions:
            txn["sender_label"] = all_labels.get(txn["sender"], 0)
            txn["receiver_label"] = all_labels.get(txn["receiver"], 0)

            writer.writerow(txn)

    print(f"Generated {len(transactions)} transactions")
    print(f"Generated {len(accounts)} accounts")
    print(f"Saved data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()