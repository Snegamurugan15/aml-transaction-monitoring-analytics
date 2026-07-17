from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RNG = np.random.default_rng(42)

LOW_RISK_COUNTRIES = ["CA", "US", "GB", "AU", "DE", "FR", "NL", "JP"]
HIGH_RISK_COUNTRIES = ["IR", "KP", "SY", "MM", "AF", "RU", "VE"]
CHANNELS = ["cash_deposit", "wire", "ach", "card", "check", "online_transfer"]


def weighted_choice(values: list[str], probabilities: list[float], size: int) -> np.ndarray:
    return RNG.choice(values, size=size, p=np.array(probabilities) / np.sum(probabilities))


def make_customers(n_customers: int = 650) -> pd.DataFrame:
    customer_ids = [f"C{idx:06d}" for idx in range(1, n_customers + 1)]
    customer_type = weighted_choice(["Personal", "Business"], [0.78, 0.22], n_customers)

    segments = []
    expected_volume = []
    industries = []
    for ctype in customer_type:
        if ctype == "Business":
            segment = weighted_choice(
                ["small_business", "corporate", "money_services", "import_export"],
                [0.62, 0.18, 0.08, 0.12],
                1,
            )[0]
            volume = float(RNG.lognormal(mean=10.5, sigma=0.65))
            industry = weighted_choice(
                ["Restaurant", "Construction", "Consulting", "Retail", "Import/Export", "Money Services"],
                [0.2, 0.18, 0.2, 0.22, 0.12, 0.08],
                1,
            )[0]
        else:
            segment = weighted_choice(["retail", "affluent", "student"], [0.7, 0.18, 0.12], 1)[0]
            volume = float(RNG.lognormal(mean=8.2, sigma=0.7))
            industry = weighted_choice(
                ["Healthcare", "Education", "Technology", "Hospitality", "Student", "Retired", "Self-employed"],
                [0.16, 0.14, 0.2, 0.14, 0.12, 0.1, 0.14],
                1,
            )[0]
        segments.append(segment)
        expected_volume.append(round(volume, 2))
        industries.append(industry)

    onboarding_offsets = RNG.integers(60, 2200, size=n_customers)
    onboarding_dates = pd.Timestamp("2026-01-01") - pd.to_timedelta(onboarding_offsets, unit="D")
    base_risk = weighted_choice(["Low", "Medium", "High"], [0.72, 0.23, 0.05], n_customers)
    countries = weighted_choice(LOW_RISK_COUNTRIES + HIGH_RISK_COUNTRIES, [18, 18, 7, 4, 5, 5, 3, 4, 1, 1, 1, 1, 1, 1, 1], n_customers)

    return pd.DataFrame(
        {
            "customer_id": customer_ids,
            "customer_type": customer_type,
            "segment": segments,
            "onboarding_date": onboarding_dates.date.astype(str),
            "customer_country": countries,
            "base_risk_rating": base_risk,
            "expected_monthly_volume": expected_volume,
            "occupation_or_industry": industries,
        }
    )


def make_normal_transactions(customers: pd.DataFrame, n_transactions: int = 16000) -> pd.DataFrame:
    customer_weights = customers["expected_monthly_volume"].to_numpy()
    customer_weights = customer_weights / customer_weights.sum()
    chosen_customers = RNG.choice(customers["customer_id"], size=n_transactions, p=customer_weights)

    start = pd.Timestamp("2026-01-01")
    minute_offsets = RNG.integers(0, 180 * 24 * 60, size=n_transactions)
    timestamps = start + pd.to_timedelta(minute_offsets, unit="m")

    channels = weighted_choice(CHANNELS, [0.16, 0.16, 0.24, 0.2, 0.08, 0.16], n_transactions)
    directions = []
    amounts = []
    countries = []
    counterparties = []

    for idx, channel in enumerate(channels):
        if channel == "cash_deposit":
            directions.append("incoming")
            amount = RNG.lognormal(mean=7.7, sigma=0.75)
        elif channel == "wire":
            directions.append(weighted_choice(["incoming", "outgoing"], [0.42, 0.58], 1)[0])
            amount = RNG.lognormal(mean=8.9, sigma=0.95)
        elif channel == "ach":
            directions.append(weighted_choice(["incoming", "outgoing"], [0.5, 0.5], 1)[0])
            amount = RNG.lognormal(mean=7.6, sigma=0.85)
        elif channel == "card":
            directions.append("outgoing")
            amount = RNG.lognormal(mean=5.6, sigma=0.9)
        elif channel == "check":
            directions.append(weighted_choice(["incoming", "outgoing"], [0.45, 0.55], 1)[0])
            amount = RNG.lognormal(mean=7.8, sigma=0.7)
        else:
            directions.append(weighted_choice(["incoming", "outgoing"], [0.48, 0.52], 1)[0])
            amount = RNG.lognormal(mean=7.2, sigma=0.8)

        if RNG.random() < 0.035:
            country = RNG.choice(HIGH_RISK_COUNTRIES)
        else:
            country = RNG.choice(LOW_RISK_COUNTRIES)

        amounts.append(round(float(np.clip(amount, 5, 85000)), 2))
        countries.append(country)
        counterparties.append(f"CP{RNG.integers(1, 3800):05d}")

    return pd.DataFrame(
        {
            "transaction_id": [f"T{idx:08d}" for idx in range(1, n_transactions + 1)],
            "customer_id": chosen_customers,
            "transaction_ts": timestamps,
            "direction": directions,
            "channel": channels,
            "amount": amounts,
            "currency": "CAD",
            "counterparty_country": countries,
            "counterparty_id": counterparties,
            "label_suspicious": 0,
            "injected_typology": "normal",
        }
    )


def inject_structuring(transactions: pd.DataFrame, customers: pd.DataFrame, next_id: int) -> tuple[pd.DataFrame, int]:
    selected = RNG.choice(customers["customer_id"], size=28, replace=False)
    rows = []
    for customer_id in selected:
        base_day = pd.Timestamp("2026-03-01") + pd.to_timedelta(int(RNG.integers(0, 90)), unit="D")
        for j in range(int(RNG.integers(4, 8))):
            rows.append(
                {
                    "transaction_id": f"T{next_id:08d}",
                    "customer_id": customer_id,
                    "transaction_ts": base_day + pd.to_timedelta(int(RNG.integers(0, 6 * 24 * 60)), unit="m"),
                    "direction": "incoming",
                    "channel": "cash_deposit",
                    "amount": round(float(RNG.uniform(9100, 9950)), 2),
                    "currency": "CAD",
                    "counterparty_country": "CA",
                    "counterparty_id": f"CP_STRUCT_{customer_id}",
                    "label_suspicious": 1,
                    "injected_typology": "structuring",
                }
            )
            next_id += 1
    return pd.concat([transactions, pd.DataFrame(rows)], ignore_index=True), next_id


def inject_rapid_movement(transactions: pd.DataFrame, customers: pd.DataFrame, next_id: int) -> tuple[pd.DataFrame, int]:
    selected = RNG.choice(customers["customer_id"], size=34, replace=False)
    rows = []
    for customer_id in selected:
        base_ts = pd.Timestamp("2026-02-01") + pd.to_timedelta(int(RNG.integers(0, 120 * 24 * 60)), unit="m")
        incoming_amount = round(float(RNG.uniform(18000, 75000)), 2)
        outgoing_amount = round(incoming_amount * float(RNG.uniform(0.78, 0.97)), 2)
        rows.extend(
            [
                {
                    "transaction_id": f"T{next_id:08d}",
                    "customer_id": customer_id,
                    "transaction_ts": base_ts,
                    "direction": "incoming",
                    "channel": "wire",
                    "amount": incoming_amount,
                    "currency": "CAD",
                    "counterparty_country": RNG.choice(LOW_RISK_COUNTRIES),
                    "counterparty_id": f"CP_IN_{customer_id}",
                    "label_suspicious": 1,
                    "injected_typology": "rapid_movement",
                },
                {
                    "transaction_id": f"T{next_id + 1:08d}",
                    "customer_id": customer_id,
                    "transaction_ts": base_ts + pd.to_timedelta(int(RNG.integers(8, 72)), unit="h"),
                    "direction": "outgoing",
                    "channel": "wire",
                    "amount": outgoing_amount,
                    "currency": "CAD",
                    "counterparty_country": weighted_choice(HIGH_RISK_COUNTRIES + LOW_RISK_COUNTRIES, [6, 6, 6, 6, 6, 6, 6, 1, 1, 1, 1, 1, 1, 1, 1], 1)[0],
                    "counterparty_id": f"CP_OUT_{customer_id}",
                    "label_suspicious": 1,
                    "injected_typology": "rapid_movement",
                },
            ]
        )
        next_id += 2
    return pd.concat([transactions, pd.DataFrame(rows)], ignore_index=True), next_id


def inject_high_risk_jurisdiction(transactions: pd.DataFrame, customers: pd.DataFrame, next_id: int) -> tuple[pd.DataFrame, int]:
    selected = RNG.choice(customers["customer_id"], size=55, replace=False)
    rows = []
    for customer_id in selected:
        for _ in range(int(RNG.integers(1, 4))):
            rows.append(
                {
                    "transaction_id": f"T{next_id:08d}",
                    "customer_id": customer_id,
                    "transaction_ts": pd.Timestamp("2026-01-15") + pd.to_timedelta(int(RNG.integers(0, 150 * 24 * 60)), unit="m"),
                    "direction": weighted_choice(["incoming", "outgoing"], [0.35, 0.65], 1)[0],
                    "channel": "wire",
                    "amount": round(float(RNG.uniform(7000, 60000)), 2),
                    "currency": "CAD",
                    "counterparty_country": RNG.choice(HIGH_RISK_COUNTRIES),
                    "counterparty_id": f"CP_HR_{RNG.integers(1, 999):04d}",
                    "label_suspicious": 1,
                    "injected_typology": "high_risk_jurisdiction",
                }
            )
            next_id += 1
    return pd.concat([transactions, pd.DataFrame(rows)], ignore_index=True), next_id


def inject_dormant_reactivation(transactions: pd.DataFrame, customers: pd.DataFrame, next_id: int) -> tuple[pd.DataFrame, int]:
    selected = RNG.choice(customers["customer_id"], size=24, replace=False)
    transactions = transactions[~transactions["customer_id"].isin(selected)].copy()
    rows = []
    for customer_id in selected:
        early_ts = pd.Timestamp("2026-01-03") + pd.to_timedelta(int(RNG.integers(0, 7 * 24 * 60)), unit="m")
        dormant_ts = pd.Timestamp("2026-05-10") + pd.to_timedelta(int(RNG.integers(0, 30 * 24 * 60)), unit="m")
        rows.extend(
            [
                {
                    "transaction_id": f"T{next_id:08d}",
                    "customer_id": customer_id,
                    "transaction_ts": early_ts,
                    "direction": "outgoing",
                    "channel": "card",
                    "amount": round(float(RNG.uniform(20, 150)), 2),
                    "currency": "CAD",
                    "counterparty_country": "CA",
                    "counterparty_id": f"CP_SMALL_{customer_id}",
                    "label_suspicious": 0,
                    "injected_typology": "normal",
                },
                {
                    "transaction_id": f"T{next_id + 1:08d}",
                    "customer_id": customer_id,
                    "transaction_ts": dormant_ts,
                    "direction": "incoming",
                    "channel": "wire",
                    "amount": round(float(RNG.uniform(24000, 90000)), 2),
                    "currency": "CAD",
                    "counterparty_country": RNG.choice(LOW_RISK_COUNTRIES),
                    "counterparty_id": f"CP_DORMANT_IN_{customer_id}",
                    "label_suspicious": 1,
                    "injected_typology": "dormant_reactivation",
                },
                {
                    "transaction_id": f"T{next_id + 2:08d}",
                    "customer_id": customer_id,
                    "transaction_ts": dormant_ts + pd.to_timedelta(int(RNG.integers(1, 48)), unit="h"),
                    "direction": "outgoing",
                    "channel": "wire",
                    "amount": round(float(RNG.uniform(18000, 85000)), 2),
                    "currency": "CAD",
                    "counterparty_country": RNG.choice(HIGH_RISK_COUNTRIES),
                    "counterparty_id": f"CP_DORMANT_OUT_{customer_id}",
                    "label_suspicious": 1,
                    "injected_typology": "dormant_reactivation",
                },
            ]
        )
        next_id += 3
    return pd.concat([transactions, pd.DataFrame(rows)], ignore_index=True), next_id


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    customers = make_customers()
    transactions = make_normal_transactions(customers)
    next_id = len(transactions) + 1

    transactions, next_id = inject_structuring(transactions, customers, next_id)
    transactions, next_id = inject_rapid_movement(transactions, customers, next_id)
    transactions, next_id = inject_high_risk_jurisdiction(transactions, customers, next_id)
    transactions, next_id = inject_dormant_reactivation(transactions, customers, next_id)

    transactions = transactions.sort_values(["transaction_ts", "transaction_id"]).reset_index(drop=True)
    transactions["transaction_ts"] = pd.to_datetime(transactions["transaction_ts"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    customers.to_csv(DATA_DIR / "synthetic_customers.csv", index=False)
    transactions.to_csv(DATA_DIR / "synthetic_transactions.csv", index=False)

    print(f"Wrote {len(customers):,} customers to {DATA_DIR / 'synthetic_customers.csv'}")
    print(f"Wrote {len(transactions):,} transactions to {DATA_DIR / 'synthetic_transactions.csv'}")
    print(f"Suspicious transaction rate: {transactions['label_suspicious'].mean():.2%}")


if __name__ == "__main__":
    main()
