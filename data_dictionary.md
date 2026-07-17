# Data Dictionary

## synthetic_customers.csv

| Field | Description |
| --- | --- |
| customer_id | Unique synthetic customer identifier. |
| customer_type | Personal or Business. |
| segment | Retail, affluent, small business, corporate, or student. |
| onboarding_date | Synthetic customer onboarding date. |
| customer_country | Customer residence or registration country. |
| base_risk_rating | Initial KYC risk rating: Low, Medium, or High. |
| expected_monthly_volume | Approximate expected customer transaction volume. |
| occupation_or_industry | Synthetic occupation or industry descriptor. |

## synthetic_transactions.csv

| Field | Description |
| --- | --- |
| transaction_id | Unique synthetic transaction identifier. |
| customer_id | Customer associated with the transaction. |
| transaction_ts | Transaction timestamp. |
| direction | Incoming or outgoing transaction flow. |
| channel | Cash, wire, ACH, card, check, or online transfer. |
| amount | Transaction amount. |
| currency | Synthetic transaction currency. |
| counterparty_country | Country associated with the counterparty or transaction destination. |
| counterparty_id | Synthetic counterparty identifier. |
| label_suspicious | Ground-truth synthetic label used for validation. |
| injected_typology | Suspicious typology injected during generation, if any. |

## scored_transactions.csv

| Field | Description |
| --- | --- |
| risk_score | Interpretable AML score from 0 to 100. |
| risk_band | Low, Medium, or High alert priority. |
| alert_reasons | Pipe-delimited reasons explaining the score. |
| amount_outlier_flag | Log-amount robust z-score exceeds threshold. |
| near_threshold_cash_flag | Cash deposit between 9000 and 9999.99. |
| high_risk_country_flag | Counterparty country appears in high-risk list. |
| rapid_movement_flag | Outgoing funds follow recent incoming funds for the same customer. |
| dormant_reactivation_flag | Unusual activity after long inactivity. |
| velocity_spike_flag | High 7-day transaction count or amount for the customer. |
