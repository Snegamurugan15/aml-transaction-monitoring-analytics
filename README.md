# Canadian AML Transaction Monitoring, EDD, and STR Analytics Project

## Project Goal

Build a Canadian AML case study from a data analyst/statistician perspective. The project monitors daily transactions, recommends Enhanced Due Diligence (EDD), identifies Suspicious Transaction Report (STR) review candidates, and produces data-driven advisory outputs for AML leadership.

This is a synthetic-data project for interview and portfolio use. It is not legal advice and does not replace institution-specific AML policies, FINTRAC guidance, or counsel review.

## Business Scenario

A Canadian financial institution needs a transparent monitoring workflow that can prioritize suspicious activity while supporting defensible investigator decisions. The analytics workflow detects:

- Structuring: repeated cash deposits just below CAD 10,000.
- Large cash activity: cash deposits at or above CAD 10,000 in a 24-hour window.
- Rapid movement of funds: incoming funds followed by outgoing wires.
- High-risk jurisdiction exposure.
- Dormant account reactivation followed by unusual activity.
- Statistical outliers relative to normal customer and channel behaviour.

## Project Structure

```text
aml_transaction_monitoring_analytics/
  data/
    synthetic_customers.csv
    synthetic_transactions.csv
  outputs/
    scored_transactions.csv
    high_risk_alerts.csv
    edd_queue.csv
    str_review_candidates.csv
    customer_risk_summary.csv
    model_validation_summary.csv
    threshold_tuning_summary.csv
    aml_dashboard_summary.xlsx
  reports/
    executive_summary.md
    edd_case_review_template.md
    str_narrative_template.md
    aml_leadership_advisory.md
  sql/
    aml_monitoring_queries.sql
  src/
    generate_synthetic_aml_data.py
    aml_risk_scoring.py
  app.py
```

## Methods Used

- Synthetic Canadian banking transaction data in CAD.
- Robust statistics using median absolute deviation on log transaction amounts.
- Rolling customer behaviour features over 24-hour and 7-day windows.
- Transparent rule-based scoring for investigator explainability.
- EDD and STR review recommendation flags.
- Precision, recall, and F1 validation against synthetic ground-truth labels.
- Excel workbook outputs for dashboarding and AML leadership review.

## Regulatory Framing

The project is built around public guidance themes:

- FINTRAC states that ML/TF indicators are potential red flags that may initiate suspicion when assessed with facts and context.
- FINTRAC expects high-quality STR narratives written in clear language that explain the suspicion and actions taken.
- FINTRAC guidance describes enhanced ongoing monitoring for clients identified as high risk.
- FATF recommendations support a risk-based approach to customer due diligence and ongoing monitoring.

Official references used while building the project:

- FINTRAC suspicious transaction reporting guidance: https://fintrac-canafe.canada.ca/guidance-directives/transaction-operation/str-dod/str-dod-eng
- FINTRAC ongoing monitoring requirements: https://fintrac-canafe.canada.ca/guidance-directives/client-clientele/omr-eng
- FINTRAC ML/TF indicators for financial entities: https://fintrac-canafe.canada.ca/guidance-directives/transaction-operation/indicators-indicateurs/fin_mltf-eng
- FINTRAC obligations and guidance under the PCMLTFA/R: https://fintrac-canafe.canada.ca/guidance-directives/guidance-directives-eng
- FATF recommendations: https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html

## How To Run

From this folder:

```powershell
python src/generate_synthetic_aml_data.py
python src/aml_risk_scoring.py
```

If the Microsoft Store Python alias appears instead of the local Python install, use:

```powershell
& 'C:\Users\Dexter\AppData\Local\Python\bin\python.exe' src/generate_synthetic_aml_data.py
& 'C:\Users\Dexter\AppData\Local\Python\bin\python.exe' src/aml_risk_scoring.py
```

## Live Dashboard

Run the Streamlit dashboard from this folder:

```powershell
streamlit run app.py
```

If the Streamlit command is not on the PATH, use:

```powershell
& 'C:\Users\Dexter\AppData\Local\Python\bin\python.exe' -m streamlit run app.py
```

## Key Outputs

- `outputs/high_risk_alerts.csv`: daily transaction monitoring alerts.
- `outputs/edd_queue.csv`: customers and transactions recommended for EDD.
- `outputs/str_review_candidates.csv`: alerts that should be reviewed for possible STR filing.
- `outputs/customer_risk_summary.csv`: customer-level case prioritization.
- `outputs/model_validation_summary.csv`: precision, recall, F1, and confusion matrix.
- `outputs/threshold_tuning_summary.csv`: score threshold tradeoffs for monitoring, EDD, and STR review.
- `outputs/aml_dashboard_summary.xlsx`: dashboard-ready workbook.
- `reports/executive_summary.md`: business-facing findings.
- `reports/edd_case_review_template.md`: EDD investigation checklist.
- `reports/str_narrative_template.md`: STR writing support template.
- `reports/aml_leadership_advisory.md`: strategic advisory memo.
