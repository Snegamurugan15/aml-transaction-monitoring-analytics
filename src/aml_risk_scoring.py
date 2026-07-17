from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
REPORT_DIR = ROOT / "reports"
HIGH_RISK_COUNTRIES = {"IR", "KP", "SY", "MM", "AF", "RU", "VE"}
REPORTING_THRESHOLD_CAD = 10000


def robust_z(series: pd.Series) -> pd.Series:
    median = series.median()
    mad = (series - median).abs().median()
    if mad == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return 0.6745 * (series - median) / mad


def add_rolling_features(transactions: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for _, group in transactions.sort_values("transaction_ts").groupby("customer_id", sort=False):
        g = group.copy().set_index("transaction_ts")
        rolling_amount = g["amount"].rolling("7D", min_periods=1).sum()
        rolling_count = g["amount"].rolling("7D", min_periods=1).count()
        near_threshold = (
            (g["channel"].eq("cash_deposit"))
            & (g["amount"].between(9000, 9999.99))
            & (g["direction"].eq("incoming"))
        ).astype(int)
        reportable_cash = g["amount"].where(g["channel"].eq("cash_deposit") & g["direction"].eq("incoming"), 0)
        g["customer_7d_amount"] = rolling_amount.to_numpy()
        g["customer_7d_txn_count"] = rolling_count.to_numpy()
        g["near_threshold_cash_7d_count"] = near_threshold.rolling("7D", min_periods=1).sum().to_numpy()
        g["cash_deposit_24h_amount"] = reportable_cash.rolling("1D", min_periods=1).sum().to_numpy()
        g["days_since_prior_txn"] = g.index.to_series().diff().dt.total_seconds().div(86400).fillna(0).to_numpy()
        frames.append(g.reset_index())
    return pd.concat(frames, ignore_index=True)


def add_rapid_movement_flag(transactions: pd.DataFrame) -> pd.DataFrame:
    transactions = transactions.sort_values(["customer_id", "transaction_ts"]).copy()
    flags = pd.Series(False, index=transactions.index)

    for _, group in transactions.groupby("customer_id", sort=False):
        incoming = group[group["direction"].eq("incoming")][["transaction_ts", "amount"]]
        for idx, row in group[group["direction"].eq("outgoing") & group["channel"].eq("wire")].iterrows():
            window = incoming[
                (incoming["transaction_ts"] >= row["transaction_ts"] - pd.Timedelta(days=3))
                & (incoming["transaction_ts"] < row["transaction_ts"])
                & (incoming["amount"] >= row["amount"] * 0.75)
            ]
            if not window.empty:
                flags.loc[idx] = True

    transactions["rapid_movement_flag"] = flags
    return transactions


def score_transactions(transactions: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    tx = transactions.merge(customers[["customer_id", "base_risk_rating", "expected_monthly_volume"]], on="customer_id", how="left")
    tx["transaction_ts"] = pd.to_datetime(tx["transaction_ts"])
    tx["log_amount"] = np.log1p(tx["amount"])
    tx["amount_robust_z"] = tx.groupby("channel")["log_amount"].transform(robust_z)
    tx = add_rolling_features(tx)
    tx = add_rapid_movement_flag(tx)

    tx["near_threshold_cash_flag"] = (
        tx["channel"].eq("cash_deposit")
        & tx["direction"].eq("incoming")
        & tx["amount"].between(9000, 9999.99)
    )
    tx["high_risk_country_flag"] = tx["counterparty_country"].isin(HIGH_RISK_COUNTRIES)
    tx["amount_outlier_flag"] = tx["amount_robust_z"].gt(3.5)
    tx["velocity_spike_flag"] = tx["customer_7d_txn_count"].ge(8) | (
        tx["customer_7d_amount"] > tx["expected_monthly_volume"] * 1.8
    )
    tx["dormant_reactivation_flag"] = tx["days_since_prior_txn"].gt(60) & tx["amount"].gt(15000)
    tx["repeat_near_threshold_flag"] = tx["near_threshold_cash_7d_count"].ge(3)
    tx["large_cash_24h_flag"] = tx["cash_deposit_24h_amount"].ge(REPORTING_THRESHOLD_CAD)
    tx["round_amount_flag"] = tx["amount"].mod(1000).eq(0) & tx["amount"].ge(5000)
    tx["kyc_high_risk_flag"] = tx["base_risk_rating"].eq("High")

    score = pd.Series(0, index=tx.index, dtype=float)
    score += tx["repeat_near_threshold_flag"].astype(int) * 30
    score += tx["near_threshold_cash_flag"].astype(int) * 18
    score += tx["rapid_movement_flag"].astype(int) * 25
    score += tx["high_risk_country_flag"].astype(int) * 20
    score += tx["dormant_reactivation_flag"].astype(int) * 18
    score += tx["velocity_spike_flag"].astype(int) * 12
    score += tx["amount_outlier_flag"].astype(int) * 10
    score += tx["large_cash_24h_flag"].astype(int) * 8
    score += tx["round_amount_flag"].astype(int) * 4
    score += tx["kyc_high_risk_flag"].astype(int) * 6
    tx["risk_score"] = score.clip(upper=100).round(0).astype(int)

    tx["risk_band"] = np.select(
        [tx["risk_score"].ge(60), tx["risk_score"].ge(35)],
        ["High", "Medium"],
        default="Low",
    )

    reason_columns = {
        "repeat_near_threshold_flag": "Repeated near-threshold cash deposits",
        "near_threshold_cash_flag": "Cash deposit below reporting threshold",
        "rapid_movement_flag": "Rapid movement of funds",
        "high_risk_country_flag": "High-risk jurisdiction exposure",
        "dormant_reactivation_flag": "Dormant account reactivation",
        "velocity_spike_flag": "7-day velocity spike",
        "amount_outlier_flag": "Statistical amount outlier",
        "large_cash_24h_flag": "Large cash activity at/above CAD 10,000 in 24 hours",
        "round_amount_flag": "Large round-dollar amount",
        "kyc_high_risk_flag": "High KYC risk rating",
    }
    tx["alert_reasons"] = tx.apply(
        lambda row: " | ".join(label for col, label in reason_columns.items() if bool(row[col])) or "No major risk indicator",
        axis=1,
    )
    tx["edd_recommended"] = tx["risk_score"].ge(60) | tx["base_risk_rating"].eq("High") | (
        tx["high_risk_country_flag"] & tx["velocity_spike_flag"]
    )
    tx["str_review_recommended"] = tx["risk_score"].ge(60) & tx["alert_reasons"].ne("No major risk indicator")
    return tx.sort_values(["risk_score", "transaction_ts"], ascending=[False, True])


def build_customer_summary(scored: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    agg = (
        scored.groupby("customer_id")
        .agg(
            max_risk_score=("risk_score", "max"),
            avg_risk_score=("risk_score", "mean"),
            high_alert_count=("risk_band", lambda s: int((s == "High").sum())),
            medium_alert_count=("risk_band", lambda s: int((s == "Medium").sum())),
            total_transaction_amount=("amount", "sum"),
            transaction_count=("transaction_id", "count"),
            suspicious_label_count=("label_suspicious", "sum"),
            edd_recommended_count=("edd_recommended", "sum"),
            str_review_recommended_count=("str_review_recommended", "sum"),
        )
        .reset_index()
    )
    top_reasons = (
        scored[scored["risk_band"].isin(["High", "Medium"])]
        .groupby("customer_id")["alert_reasons"]
        .agg(lambda s: "; ".join(pd.Series(s).value_counts().head(3).index))
        .reset_index(name="top_alert_reasons")
    )
    summary = customers.merge(agg, on="customer_id", how="left").merge(top_reasons, on="customer_id", how="left")
    summary[["max_risk_score", "avg_risk_score", "high_alert_count", "medium_alert_count", "total_transaction_amount", "transaction_count", "suspicious_label_count", "edd_recommended_count", "str_review_recommended_count"]] = summary[
        ["max_risk_score", "avg_risk_score", "high_alert_count", "medium_alert_count", "total_transaction_amount", "transaction_count", "suspicious_label_count", "edd_recommended_count", "str_review_recommended_count"]
    ].fillna(0)
    summary["case_priority"] = np.select(
        [summary["high_alert_count"].ge(2), summary["max_risk_score"].ge(60), summary["medium_alert_count"].ge(3)],
        ["Priority 1", "Priority 2", "Priority 3"],
        default="Monitor",
    )
    return summary.sort_values(["case_priority", "max_risk_score", "high_alert_count"], ascending=[True, False, False])


def validation_summary(scored: pd.DataFrame, threshold: int = 60) -> pd.DataFrame:
    predicted = scored["risk_score"].ge(threshold)
    actual = scored["label_suspicious"].eq(1)
    tp = int((predicted & actual).sum())
    fp = int((predicted & ~actual).sum())
    fn = int((~predicted & actual).sum())
    tn = int((~predicted & ~actual).sum())
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

    return pd.DataFrame(
        [
            {"metric": "threshold", "value": threshold},
            {"metric": "true_positive", "value": tp},
            {"metric": "false_positive", "value": fp},
            {"metric": "false_negative", "value": fn},
            {"metric": "true_negative", "value": tn},
            {"metric": "precision", "value": round(precision, 4)},
            {"metric": "recall", "value": round(recall, 4)},
            {"metric": "f1_score", "value": round(f1, 4)},
        ]
    )


def threshold_tuning_summary(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    actual = scored["label_suspicious"].eq(1)
    for threshold, queue_name in [(25, "Broad monitoring review"), (35, "Medium-and-high alert review"), (50, "Enhanced review"), (60, "STR review candidate")]:
        predicted = scored["risk_score"].ge(threshold)
        tp = int((predicted & actual).sum())
        fp = int((predicted & ~actual).sum())
        fn = int((~predicted & actual).sum())
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        rows.append(
            {
                "queue_name": queue_name,
                "risk_score_threshold": threshold,
                "predicted_alerts": int(predicted.sum()),
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
            }
        )
    return pd.DataFrame(rows)


def write_excel_summary(scored: pd.DataFrame, customer_summary: pd.DataFrame, validation: pd.DataFrame, threshold_tuning: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    edd_queue = scored[scored["edd_recommended"]].copy()
    str_candidates = scored[scored["str_review_recommended"]].copy()
    typology_summary = (
        scored.groupby(["risk_band", "injected_typology"])
        .size()
        .reset_index(name="transaction_count")
        .sort_values(["risk_band", "transaction_count"], ascending=[True, False])
    )
    reason_summary = (
        scored[scored["risk_band"].isin(["High", "Medium"])]["alert_reasons"]
        .str.get_dummies(sep=" | ")
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    reason_summary.columns = ["alert_reason", "count"]

    with pd.ExcelWriter(OUTPUT_DIR / "aml_dashboard_summary.xlsx", engine="openpyxl") as writer:
        scored.head(500).to_excel(writer, sheet_name="Top Scored Transactions", index=False)
        edd_queue.head(500).to_excel(writer, sheet_name="EDD Queue", index=False)
        str_candidates.head(500).to_excel(writer, sheet_name="STR Review Candidates", index=False)
        customer_summary.head(200).to_excel(writer, sheet_name="Customer Risk Ranking", index=False)
        typology_summary.to_excel(writer, sheet_name="Typology Summary", index=False)
        reason_summary.to_excel(writer, sheet_name="Alert Reason Summary", index=False)
        validation.to_excel(writer, sheet_name="Validation", index=False)
        threshold_tuning.to_excel(writer, sheet_name="Threshold Tuning", index=False)


def write_report(scored: pd.DataFrame, customer_summary: pd.DataFrame, validation: pd.DataFrame, threshold_tuning: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    high_alerts = scored[scored["risk_band"].eq("High")]
    medium_alerts = scored[scored["risk_band"].eq("Medium")]
    precision = validation.loc[validation["metric"].eq("precision"), "value"].iloc[0]
    recall = validation.loc[validation["metric"].eq("recall"), "value"].iloc[0]
    f1 = validation.loc[validation["metric"].eq("f1_score"), "value"].iloc[0]
    monitoring_row = threshold_tuning[threshold_tuning["risk_score_threshold"].eq(35)].iloc[0]

    top_reasons = (
        high_alerts["alert_reasons"]
        .str.get_dummies(sep=" | ")
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    reason_lines = "\n".join([f"- {reason}: {int(count)} high-risk transactions" for reason, count in top_reasons.items()])
    priority_customers = customer_summary[customer_summary["case_priority"].eq("Priority 1")].head(10)
    customer_lines = "\n".join(
        [
            f"- {row.customer_id}: max score {int(row.max_risk_score)}, high alerts {int(row.high_alert_count)}, reason: {row.top_alert_reasons}"
            for row in priority_customers.itertuples()
        ]
    )

    report = f"""# Executive Summary: AML Transaction Monitoring Analytics

## Objective

Identify and prioritize transactions that may require AML investigation using explainable statistical and rule-based indicators.

## Key Results

- Transactions scored: {len(scored):,}
- High-risk alerts: {len(high_alerts):,}
- Medium-risk alerts: {len(medium_alerts):,}
- Customers marked Priority 1: {int((customer_summary["case_priority"] == "Priority 1").sum()):,}
- Validation at score >= 60: precision {precision}, recall {recall}, F1 {f1}
- Monitoring queue at score >= 35: precision {monitoring_row.precision}, recall {monitoring_row.recall}, alerts {int(monitoring_row.predicted_alerts):,}

## Main Alert Drivers

{reason_lines}

## Highest Priority Customers

{customer_lines}

## Analyst Interpretation

The scoring logic is intentionally transparent. Each high-risk transaction includes a reason string that can be reviewed by an AML investigator, model validator, or compliance stakeholder. The system emphasizes behavior-based indicators such as repeated near-threshold cash deposits, fast movement of funds, high-risk jurisdiction exposure, unusual reactivation after dormancy, and Canadian large-cash aggregation at or above CAD 10,000 in 24 hours.

## EDD and STR Workflow

- Enhanced Due Diligence is recommended when the customer has high transaction risk, high KYC risk, or combined high-risk geography and velocity indicators.
- STR review is recommended when the transaction meets the high-risk score threshold and the alert rationale supports reasonable grounds to suspect.
- Large cash aggregation is highlighted separately because it can create a reporting obligation even when the transaction narrative does not independently support suspicion.

## Recommended Next Steps

- Tune risk score thresholds based on investigator capacity and desired recall.
- Add negative news, sanctions screening, and customer due diligence attributes if available.
- Build a Power BI or Tableau dashboard from the Excel workbook and CSV outputs.
- Track investigator dispositions to convert this from rules-based scoring to supervised model development.
- Use reviewed case outcomes to refine EDD triggers, STR narrative quality checks, and leadership reporting.
"""
    (REPORT_DIR / "executive_summary.md").write_text(report, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    transactions = pd.read_csv(DATA_DIR / "synthetic_transactions.csv")
    customers = pd.read_csv(DATA_DIR / "synthetic_customers.csv")

    scored = score_transactions(transactions, customers)
    customer_summary = build_customer_summary(scored, customers)
    validation = validation_summary(scored, threshold=60)
    threshold_tuning = threshold_tuning_summary(scored)

    scored.to_csv(OUTPUT_DIR / "scored_transactions.csv", index=False)
    scored[scored["risk_band"].eq("High")].to_csv(OUTPUT_DIR / "high_risk_alerts.csv", index=False)
    scored[scored["edd_recommended"]].to_csv(OUTPUT_DIR / "edd_queue.csv", index=False)
    scored[scored["str_review_recommended"]].to_csv(OUTPUT_DIR / "str_review_candidates.csv", index=False)
    customer_summary.to_csv(OUTPUT_DIR / "customer_risk_summary.csv", index=False)
    validation.to_csv(OUTPUT_DIR / "model_validation_summary.csv", index=False)
    threshold_tuning.to_csv(OUTPUT_DIR / "threshold_tuning_summary.csv", index=False)
    write_excel_summary(scored, customer_summary, validation, threshold_tuning)
    write_report(scored, customer_summary, validation, threshold_tuning)

    print(f"Wrote scored transactions to {OUTPUT_DIR / 'scored_transactions.csv'}")
    print(f"Wrote high-risk alerts to {OUTPUT_DIR / 'high_risk_alerts.csv'}")
    print(f"Wrote EDD queue to {OUTPUT_DIR / 'edd_queue.csv'}")
    print(f"Wrote STR review candidates to {OUTPUT_DIR / 'str_review_candidates.csv'}")
    print(f"Wrote customer summary to {OUTPUT_DIR / 'customer_risk_summary.csv'}")
    print(f"Wrote validation summary to {OUTPUT_DIR / 'model_validation_summary.csv'}")
    print(f"Wrote threshold tuning summary to {OUTPUT_DIR / 'threshold_tuning_summary.csv'}")
    print(f"Wrote Excel workbook to {OUTPUT_DIR / 'aml_dashboard_summary.xlsx'}")
    print(f"Wrote report to {REPORT_DIR / 'executive_summary.md'}")


if __name__ == "__main__":
    main()
