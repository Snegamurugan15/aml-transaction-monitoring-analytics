# Executive Summary: AML Transaction Monitoring Analytics

## Objective

Identify and prioritize transactions that may require AML investigation using explainable statistical and rule-based indicators.

## Key Results

- Transactions scored: 15,891
- High-risk alerts: 94
- Medium-risk alerts: 267
- Customers marked Priority 1: 25
- Validation at score >= 60: precision 0.9574, recall 0.24, F1 0.3838
- Monitoring queue at score >= 35: precision 0.4875, recall 0.4693, alerts 361

## Main Alert Drivers

- Repeated near-threshold cash deposits: 94 high-risk transactions
- 7-day velocity spike: 93 high-risk transactions
- Cash deposit below reporting threshold: 91 high-risk transactions
- Large cash activity at/above CAD 10,000 in 24 hours: 62 high-risk transactions
- High KYC risk rating: 6 high-risk transactions

## Highest Priority Customers

- C000101: max score 74, high alerts 4, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours | High KYC risk rating; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | High KYC risk rating; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | Large cash activity at/above CAD 10,000 in 24 hours | High KYC risk rating
- C000508: max score 68, high alerts 7, reason: Rapid movement of funds | 7-day velocity spike; Repeated near-threshold cash deposits | 7-day velocity spike; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours
- C000097: max score 68, high alerts 5, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike; Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours
- C000195: max score 68, high alerts 5, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike; Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours
- C000204: max score 68, high alerts 5, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike; Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours
- C000324: max score 68, high alerts 5, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike
- C000413: max score 68, high alerts 5, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours; Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours
- C000602: max score 68, high alerts 5, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike; Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours
- C000029: max score 68, high alerts 4, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours; Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike; Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours
- C000130: max score 68, high alerts 4, reason: Repeated near-threshold cash deposits | Cash deposit below reporting threshold | 7-day velocity spike | Large cash activity at/above CAD 10,000 in 24 hours

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
