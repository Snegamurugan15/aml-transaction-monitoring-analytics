# Dashboard Explanation Artifact

## Project Name

Canadian AML Transaction Monitoring, EDD, and STR Review Dashboard

## Purpose Of The Dashboard

This dashboard helps an AML team quickly review bank transactions and identify activity that may need investigation. It highlights high-risk transactions, customers needing Enhanced Due Diligence (EDD), and cases that may require Suspicious Transaction Report (STR) review.

## Data Used

The dashboard uses synthetic banking data created for this project. No real customer or bank data is used.

Main data files:

- `scored_transactions.csv`: all transactions with AML risk scores.
- `customer_risk_summary.csv`: customer-level risk summary.
- `edd_queue.csv`: transactions and customers recommended for EDD.
- `str_review_candidates.csv`: transactions recommended for STR review.
- `threshold_tuning_summary.csv`: scoring threshold performance.

## Sidebar Filters

The left sidebar allows the user to narrow down the dashboard view.

Filters include:

- Date range: choose the transaction period to review.
- Review queue: view all transactions, high-risk alerts, EDD queue, or STR candidates.
- Minimum risk score: show only transactions above a selected risk score.
- Risk band: filter by High, Medium, or Low risk.
- Channel: filter by cash deposit, wire, ACH, card, check, or online transfer.
- Typology: filter by suspicious pattern type.
- Customer ID search: look up a specific customer.

## KPI Section

The top row gives a quick summary of AML activity.

It shows:

- Visible transactions: number of transactions after filters are applied.
- Transaction value: total CAD value of filtered transactions.
- High-risk alerts: transactions that need urgent review.
- EDD queue: transactions or customers recommended for deeper due diligence.
- STR review: cases that may need suspicious transaction reporting review.
- STR precision: how accurate the high-risk STR queue is in the synthetic test data.

## Monitoring Tab

This tab gives the daily transaction monitoring view.

It shows:

- A daily bar chart of transactions by risk level.
- A breakdown of High, Medium, and Low risk transactions.
- A queue summary for high-risk alerts, EDD records, and STR review candidates.

In simple terms, this tab answers: "What does today's AML workload look like?"

## Alert Drivers Tab

This tab explains why transactions are being flagged.

It shows:

- Top alert reasons, such as near-threshold cash deposits, rapid fund movement, high-risk country exposure, or dormant account reactivation.
- Countries connected to medium and high-risk alerts.

In simple terms, this tab answers: "What suspicious patterns are driving alerts?"

## Customer Risk Tab

This tab focuses on customers instead of individual transactions.

It shows:

- Top customers by maximum AML risk score.
- Customer type, segment, base KYC risk rating, priority level, EDD count, STR count, and alert reasons.

In simple terms, this tab answers: "Which customers should the AML team review first?"

## EDD & STR Tab

This tab supports investigation and regulatory reporting workflows.

EDD Queue section:

- Shows customers and transactions recommended for Enhanced Due Diligence.
- Helps analysts review customer profile, risk rating, transaction behavior, and alert reasons.

STR Review Candidates section:

- Shows high-risk transactions that may need STR review.
- Provides a draft narrative support box to help explain why the activity looks suspicious.

In simple terms, this tab answers: "Which cases need deeper review or possible reporting?"

## Thresholds Tab

This tab helps AML leadership understand how changing the risk score threshold affects workload and accuracy.

It compares:

- Broad monitoring review.
- Medium-and-high alert review.
- Enhanced review.
- STR review candidate threshold.

It shows:

- Predicted alert volume.
- Precision.
- Recall.
- F1 score.

In simple terms, this tab answers: "Should we review more cases to catch more suspicious activity, or fewer cases with higher confidence?"

## Data Tab

This tab shows the filtered transaction-level data.

It includes:

- Transaction timestamp.
- Transaction ID.
- Customer ID.
- Risk score.
- Risk band.
- Amount.
- Channel.
- Direction.
- Counterparty country.
- Typology.
- EDD recommendation.
- STR review recommendation.
- Alert reasons.

It also allows the user to download the filtered transactions as a CSV file.

In simple terms, this tab answers: "What are the exact transactions behind the dashboard?"

## AML Workflow Shown By The Dashboard

1. Monitor transactions daily.
2. Score each transaction based on AML risk indicators.
3. Prioritize high-risk alerts.
4. Send higher-risk customers to EDD review.
5. Identify transactions that may need STR review.
6. Use threshold metrics to advise AML leadership.
7. Export filtered data for investigation or reporting.

## Key AML Concepts Demonstrated

- Transaction monitoring.
- Enhanced Due Diligence.
- STR review support.
- FINTRAC-aligned suspicious activity indicators.
- CAD 10,000 cash activity monitoring.
- High-risk jurisdiction exposure.
- Rapid movement of funds.
- Structuring behavior.
- Dormant account reactivation.
- Risk scoring and threshold tuning.

## Business Value

The dashboard helps AML teams work faster by turning large transaction data into clear review queues. It supports better investigation decisions, helps explain why alerts were created, and gives leadership useful information about workload, risk trends, and monitoring performance.

## Interview Explanation

I built a live AML dashboard using synthetic Canadian banking data. The dashboard helps identify suspicious transactions, customers needing EDD, and possible STR review candidates. It includes filters, risk score KPIs, alert reason charts, customer risk rankings, EDD and STR queues, and threshold tuning metrics. This shows my ability to combine data analysis, AML knowledge, compliance thinking, and dashboard reporting into one practical project.
