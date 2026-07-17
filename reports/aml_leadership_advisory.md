# AML Leadership Advisory Memo

## Subject

Transaction monitoring, EDD, and STR review prioritization using synthetic Canadian banking data.

## Key Advisory Points

- Prioritize investigator capacity toward high-risk alerts with multiple indicators rather than single-factor alerts.
- Separate operational queues for EDD, STR review, and large-cash monitoring to avoid mixing different compliance decisions.
- Tune thresholds using both recall and false-positive rate because excessive low-quality alerts can reduce investigator effectiveness.
- Add investigator disposition outcomes to create a feedback loop for model tuning and quality assurance.
- Monitor typology concentration weekly to identify emerging patterns, channel risk, or customer segments requiring control changes.

## Recommended Leadership Metrics

| Metric | Purpose |
| --- | --- |
| High-risk alerts per day | Tracks monitoring workload. |
| STR review candidates | Measures potential regulatory reporting workload. |
| EDD queue volume | Tracks enhanced review demand. |
| Alert-to-STR conversion rate | Measures alert quality. |
| False positive rate | Identifies tuning opportunities. |
| Top alert reasons | Shows typology trends. |
| Aging EDD cases | Monitors operational backlog. |

## Operational Recommendation

Use the current rules as a transparent baseline. After investigator outcomes are collected, calibrate thresholds and consider supervised modelling only if labels are consistent, explainability is preserved, and model governance requirements are satisfied.
