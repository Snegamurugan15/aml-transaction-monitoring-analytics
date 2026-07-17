from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
RISK_ORDER = ["High", "Medium", "Low"]
RISK_COLORS = ["#b42318", "#b54708", "#027a48"]


st.set_page_config(
    page_title="Canadian AML Monitoring Dashboard",
    page_icon="AML",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scored = pd.read_csv(OUTPUT_DIR / "scored_transactions.csv", parse_dates=["transaction_ts"])
    customers = pd.read_csv(DATA_DIR / "synthetic_customers.csv")
    customer_summary = pd.read_csv(OUTPUT_DIR / "customer_risk_summary.csv")
    validation = pd.read_csv(OUTPUT_DIR / "model_validation_summary.csv")
    thresholds = pd.read_csv(OUTPUT_DIR / "threshold_tuning_summary.csv")

    bool_columns = [
        "rapid_movement_flag",
        "near_threshold_cash_flag",
        "high_risk_country_flag",
        "amount_outlier_flag",
        "velocity_spike_flag",
        "dormant_reactivation_flag",
        "repeat_near_threshold_flag",
        "large_cash_24h_flag",
        "round_amount_flag",
        "kyc_high_risk_flag",
        "edd_recommended",
        "str_review_recommended",
    ]
    for column in bool_columns:
        if column in scored.columns and scored[column].dtype != bool:
            scored[column] = scored[column].astype(str).str.lower().eq("true")

    scored["transaction_date"] = scored["transaction_ts"].dt.date
    scored["amount"] = pd.to_numeric(scored["amount"], errors="coerce").fillna(0)
    scored["risk_score"] = pd.to_numeric(scored["risk_score"], errors="coerce").fillna(0)
    customer_summary["max_risk_score"] = pd.to_numeric(customer_summary["max_risk_score"], errors="coerce").fillna(0)
    return scored, customers, customer_summary, validation, thresholds


def money(value: float) -> str:
    return f"CAD ${value:,.0f}"


def percent(value: float) -> str:
    return f"{value:.1%}"


def metric_value(validation: pd.DataFrame, metric: str) -> float:
    match = validation.loc[validation["metric"].eq(metric), "value"]
    return float(match.iloc[0]) if not match.empty else 0.0


def split_reasons(frame: pd.DataFrame) -> pd.DataFrame:
    reasons = (
        frame["alert_reasons"]
        .dropna()
        .str.split(" | ", regex=False)
        .explode()
        .loc[lambda s: s.ne("No major risk indicator")]
    )
    if reasons.empty:
        return pd.DataFrame({"alert_reason": [], "count": []})
    return reasons.value_counts().head(12).rename_axis("alert_reason").reset_index(name="count")


def compact_table(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    visible = frame[[column for column in columns if column in frame.columns]].copy()
    if "transaction_ts" in visible.columns:
        visible["transaction_ts"] = pd.to_datetime(visible["transaction_ts"]).dt.strftime("%Y-%m-%d %H:%M")
    if "amount" in visible.columns:
        visible["amount"] = visible["amount"].map(lambda value: f"CAD ${value:,.2f}")
    return visible


def apply_filters(scored: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("AML Filters")

    min_date = scored["transaction_ts"].min().date()
    max_date = scored["transaction_ts"].max().date()
    selected_dates = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date, end_date = min_date, max_date

    queue = st.sidebar.selectbox(
        "Review queue",
        ["All transactions", "High-risk alerts", "EDD queue", "STR review candidates"],
    )
    min_score = st.sidebar.slider("Minimum risk score", 0, 100, 0, 5)
    risk_bands = st.sidebar.multiselect("Risk band", RISK_ORDER, default=RISK_ORDER)
    channels = st.sidebar.multiselect(
        "Channel",
        sorted(scored["channel"].dropna().unique()),
        default=sorted(scored["channel"].dropna().unique()),
    )
    typologies = st.sidebar.multiselect(
        "Typology",
        sorted(scored["injected_typology"].dropna().unique()),
        default=sorted(scored["injected_typology"].dropna().unique()),
    )
    customer_search = st.sidebar.text_input("Customer ID contains").strip().upper()

    filtered = scored[
        scored["transaction_date"].between(start_date, end_date)
        & scored["risk_band"].isin(risk_bands)
        & scored["channel"].isin(channels)
        & scored["injected_typology"].isin(typologies)
        & scored["risk_score"].ge(min_score)
    ].copy()

    if queue == "High-risk alerts":
        filtered = filtered[filtered["risk_band"].eq("High")]
    elif queue == "EDD queue":
        filtered = filtered[filtered["edd_recommended"]]
    elif queue == "STR review candidates":
        filtered = filtered[filtered["str_review_recommended"]]

    if customer_search:
        filtered = filtered[filtered["customer_id"].str.upper().str.contains(customer_search, regex=False)]

    return filtered


def render_kpis(filtered: pd.DataFrame, scored: pd.DataFrame, validation: pd.DataFrame) -> None:
    high_alerts = int(filtered["risk_band"].eq("High").sum())
    edd_count = int(filtered["edd_recommended"].sum())
    str_count = int(filtered["str_review_recommended"].sum())
    total_amount = filtered["amount"].sum()
    alert_rate = high_alerts / len(filtered) if len(filtered) else 0

    cols = st.columns(6)
    cols[0].metric("Visible transactions", f"{len(filtered):,}", f"{len(scored):,} total")
    cols[1].metric("Transaction value", money(total_amount))
    cols[2].metric("High-risk alerts", f"{high_alerts:,}", percent(alert_rate))
    cols[3].metric("EDD queue", f"{edd_count:,}")
    cols[4].metric("STR review", f"{str_count:,}")
    cols[5].metric("STR precision", percent(metric_value(validation, "precision")))


def render_overview(filtered: pd.DataFrame) -> None:
    left, right = st.columns([1.6, 1])

    with left:
        daily = (
            filtered.groupby(["transaction_date", "risk_band"], as_index=False)
            .agg(transactions=("transaction_id", "count"), amount=("amount", "sum"))
            .sort_values("transaction_date")
        )
        if not daily.empty:
            chart = (
                alt.Chart(daily)
                .mark_bar()
                .encode(
                    x=alt.X("transaction_date:T", title="Date"),
                    y=alt.Y("transactions:Q", title="Transactions"),
                    color=alt.Color("risk_band:N", title="Risk band", sort=RISK_ORDER, scale=alt.Scale(domain=RISK_ORDER, range=RISK_COLORS)),
                    tooltip=[
                        alt.Tooltip("transaction_date:T", title="Date"),
                        alt.Tooltip("risk_band:N", title="Risk band"),
                        alt.Tooltip("transactions:Q", title="Transactions", format=","),
                        alt.Tooltip("amount:Q", title="Amount", format="$,.0f"),
                    ],
                )
                .properties(height=340)
            )
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No transactions match the selected filters.")

    with right:
        band_counts = filtered["risk_band"].value_counts().reindex(RISK_ORDER, fill_value=0).rename_axis("risk_band").reset_index(name="transactions")
        band_chart = (
            alt.Chart(band_counts)
            .mark_bar()
            .encode(
                y=alt.Y("risk_band:N", title="Risk band", sort=RISK_ORDER),
                x=alt.X("transactions:Q", title="Transactions"),
                color=alt.Color("risk_band:N", legend=None, sort=RISK_ORDER, scale=alt.Scale(domain=RISK_ORDER, range=RISK_COLORS)),
                tooltip=[alt.Tooltip("risk_band:N"), alt.Tooltip("transactions:Q", format=",")],
            )
            .properties(height=160)
        )
        st.altair_chart(band_chart, width="stretch")

        queue_counts = pd.DataFrame(
            {
                "queue": ["High-risk alerts", "EDD queue", "STR review"],
                "records": [
                    int(filtered["risk_band"].eq("High").sum()),
                    int(filtered["edd_recommended"].sum()),
                    int(filtered["str_review_recommended"].sum()),
                ],
            }
        )
        queue_chart = (
            alt.Chart(queue_counts)
            .mark_bar(color="#2f6fed")
            .encode(
                y=alt.Y("queue:N", title=None, sort="-x"),
                x=alt.X("records:Q", title="Records"),
                tooltip=[alt.Tooltip("queue:N"), alt.Tooltip("records:Q", format=",")],
            )
            .properties(height=160)
        )
        st.altair_chart(queue_chart, width="stretch")


def render_alert_drivers(filtered: pd.DataFrame) -> None:
    left, right = st.columns([1.2, 1])

    with left:
        reason_counts = split_reasons(filtered)
        if not reason_counts.empty:
            chart = (
                alt.Chart(reason_counts)
                .mark_bar(color="#5b5fc7")
                .encode(
                    y=alt.Y("alert_reason:N", title=None, sort="-x"),
                    x=alt.X("count:Q", title="Alert count"),
                    tooltip=[alt.Tooltip("alert_reason:N", title="Alert reason"), alt.Tooltip("count:Q", title="Count", format=",")],
                )
                .properties(height=360)
            )
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No alert reasons in the selected view.")

    with right:
        country_counts = (
            filtered[filtered["risk_band"].isin(["High", "Medium"])]
            .groupby("counterparty_country", as_index=False)
            .agg(alerts=("transaction_id", "count"), amount=("amount", "sum"))
            .sort_values("alerts", ascending=False)
            .head(12)
        )
        if not country_counts.empty:
            chart = (
                alt.Chart(country_counts)
                .mark_bar(color="#008c95")
                .encode(
                    x=alt.X("alerts:Q", title="Medium/high alerts"),
                    y=alt.Y("counterparty_country:N", title="Country", sort="-x"),
                    tooltip=[
                        alt.Tooltip("counterparty_country:N", title="Country"),
                        alt.Tooltip("alerts:Q", title="Alerts", format=","),
                        alt.Tooltip("amount:Q", title="Amount", format="$,.0f"),
                    ],
                )
                .properties(height=360)
            )
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No medium or high-risk country exposure in this view.")


def render_customer_risk(filtered: pd.DataFrame, customer_summary: pd.DataFrame) -> None:
    visible_customers = filtered["customer_id"].drop_duplicates()
    summary = customer_summary[customer_summary["customer_id"].isin(visible_customers)].copy()
    summary = summary.sort_values(["max_risk_score", "high_alert_count"], ascending=False)

    chart_data = summary.head(20)
    if not chart_data.empty:
        chart = (
            alt.Chart(chart_data)
            .mark_bar(color="#7a5af8")
            .encode(
                y=alt.Y("customer_id:N", title="Customer", sort="-x"),
                x=alt.X("max_risk_score:Q", title="Max risk score", scale=alt.Scale(domain=[0, 100])),
                tooltip=[
                    alt.Tooltip("customer_id:N", title="Customer"),
                    alt.Tooltip("case_priority:N", title="Priority"),
                    alt.Tooltip("max_risk_score:Q", title="Max score", format=".0f"),
                    alt.Tooltip("high_alert_count:Q", title="High alerts", format=","),
                    alt.Tooltip("edd_recommended_count:Q", title="EDD records", format=","),
                    alt.Tooltip("str_review_recommended_count:Q", title="STR records", format=","),
                ],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("No customer risk records match the selected filters.")

    st.dataframe(
        summary[
            [
                "customer_id",
                "customer_type",
                "segment",
                "base_risk_rating",
                "case_priority",
                "max_risk_score",
                "high_alert_count",
                "edd_recommended_count",
                "str_review_recommended_count",
                "top_alert_reasons",
            ]
        ].head(100),
        width="stretch",
        hide_index=True,
    )


def render_edd_str(filtered: pd.DataFrame, customer_summary: pd.DataFrame) -> None:
    edd_frame = filtered[filtered["edd_recommended"]].sort_values(["risk_score", "transaction_ts"], ascending=[False, True])
    str_frame = filtered[filtered["str_review_recommended"]].sort_values(["risk_score", "amount"], ascending=[False, False])
    left, right = st.columns(2)

    with left:
        st.subheader("EDD Queue")
        st.dataframe(
            compact_table(
                edd_frame.head(50),
                [
                    "transaction_ts",
                    "customer_id",
                    "risk_score",
                    "risk_band",
                    "amount",
                    "channel",
                    "counterparty_country",
                    "alert_reasons",
                ],
            ),
            width="stretch",
            hide_index=True,
        )

        if not edd_frame.empty:
            selected_customer = st.selectbox("EDD customer", edd_frame["customer_id"].drop_duplicates().tolist())
            customer_row = customer_summary[customer_summary["customer_id"].eq(selected_customer)]
            if not customer_row.empty:
                st.dataframe(
                    customer_row[
                        [
                            "customer_id",
                            "customer_type",
                            "segment",
                            "base_risk_rating",
                            "case_priority",
                            "expected_monthly_volume",
                            "max_risk_score",
                            "top_alert_reasons",
                        ]
                    ],
                    width="stretch",
                    hide_index=True,
                )

    with right:
        st.subheader("STR Review Candidates")
        st.dataframe(
            compact_table(
                str_frame.head(50),
                [
                    "transaction_ts",
                    "transaction_id",
                    "customer_id",
                    "risk_score",
                    "amount",
                    "channel",
                    "direction",
                    "counterparty_country",
                    "alert_reasons",
                ],
            ),
            width="stretch",
            hide_index=True,
        )

        if not str_frame.empty:
            options = [
                f"{row.transaction_id} | {row.customer_id} | score {int(row.risk_score)} | {money(row.amount)}"
                for row in str_frame.head(200).itertuples()
            ]
            selected = st.selectbox("STR candidate", options)
            selected_txn = selected.split(" | ", 1)[0]
            row = str_frame[str_frame["transaction_id"].eq(selected_txn)].iloc[0]
            customer = customer_summary[customer_summary["customer_id"].eq(row["customer_id"])]
            profile = customer.iloc[0] if not customer.empty else None
            profile_text = (
                f"{profile['customer_type']} customer in {profile['segment']} segment with {profile['base_risk_rating']} base KYC risk"
                if profile is not None
                else "customer profile unavailable"
            )
            narrative = (
                f"Customer {row['customer_id']} generated a high-risk transaction monitoring alert on "
                f"{row['transaction_ts']:%Y-%m-%d}. The transaction was a {row['direction']} {row['channel']} "
                f"for CAD ${row['amount']:,.2f} involving counterparty country {row['counterparty_country']}. "
                f"The customer profile is {profile_text}. The alert rationale is: {row['alert_reasons']}. "
                "Based on the facts and context, the case should be reviewed to determine whether reasonable "
                "grounds to suspect money laundering or terrorist financing are present."
            )
            st.text_area("Draft STR narrative support", narrative, height=180)


def render_thresholds(thresholds: pd.DataFrame) -> None:
    metric_data = thresholds.melt(
        id_vars=["queue_name", "risk_score_threshold", "predicted_alerts"],
        value_vars=["precision", "recall", "f1_score"],
        var_name="metric",
        value_name="value",
    )
    left, right = st.columns([1.2, 1])
    with left:
        chart = (
            alt.Chart(metric_data)
            .mark_line(point=True)
            .encode(
                x=alt.X("risk_score_threshold:Q", title="Risk score threshold"),
                y=alt.Y("value:Q", title="Metric", scale=alt.Scale(domain=[0, 1])),
                color=alt.Color("metric:N", title="Metric"),
                tooltip=[
                    alt.Tooltip("queue_name:N", title="Queue"),
                    alt.Tooltip("risk_score_threshold:Q", title="Threshold"),
                    alt.Tooltip("metric:N", title="Metric"),
                    alt.Tooltip("value:Q", title="Value", format=".2%"),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(chart, width="stretch")

    with right:
        volume_chart = (
            alt.Chart(thresholds)
            .mark_bar(color="#2f6fed")
            .encode(
                y=alt.Y("queue_name:N", title=None, sort="-x"),
                x=alt.X("predicted_alerts:Q", title="Predicted alerts"),
                tooltip=[
                    alt.Tooltip("queue_name:N", title="Queue"),
                    alt.Tooltip("risk_score_threshold:Q", title="Threshold"),
                    alt.Tooltip("predicted_alerts:Q", title="Alerts", format=","),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(volume_chart, width="stretch")

    st.dataframe(thresholds, width="stretch", hide_index=True)


def render_data_explorer(filtered: pd.DataFrame) -> None:
    columns = [
        "transaction_ts",
        "transaction_id",
        "customer_id",
        "risk_score",
        "risk_band",
        "amount",
        "channel",
        "direction",
        "counterparty_country",
        "injected_typology",
        "edd_recommended",
        "str_review_recommended",
        "alert_reasons",
    ]
    visible = filtered[[column for column in columns if column in filtered.columns]].sort_values(
        ["risk_score", "transaction_ts"], ascending=[False, True]
    )
    st.dataframe(visible, width="stretch", hide_index=True)
    st.download_button(
        "Download filtered transactions",
        visible.to_csv(index=False).encode("utf-8"),
        file_name="filtered_aml_transactions.csv",
        mime="text/csv",
    )


def main() -> None:
    try:
        scored, _, customer_summary, validation, thresholds = load_data()
    except FileNotFoundError as exc:
        st.error(f"Missing project output: {exc.filename}")
        st.stop()

    st.title("Canadian AML Monitoring Dashboard")
    st.caption("Transaction monitoring, EDD queueing, STR review candidates, and leadership metrics")

    filtered = apply_filters(scored)
    render_kpis(filtered, scored, validation)

    tabs = st.tabs(["Monitoring", "Alert Drivers", "Customer Risk", "EDD & STR", "Thresholds", "Data"])
    with tabs[0]:
        render_overview(filtered)
    with tabs[1]:
        render_alert_drivers(filtered)
    with tabs[2]:
        render_customer_risk(filtered, customer_summary)
    with tabs[3]:
        render_edd_str(filtered, customer_summary)
    with tabs[4]:
        render_thresholds(thresholds)
    with tabs[5]:
        render_data_explorer(filtered)


if __name__ == "__main__":
    main()
