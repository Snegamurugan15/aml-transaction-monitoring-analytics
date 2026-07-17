-- AML Transaction Monitoring Analyst Queries
-- Dialect: ANSI-style SQL. Minor syntax changes may be needed by database.

-- 1. Transactions just below a 10,000 reporting threshold.
SELECT
    customer_id,
    transaction_id,
    transaction_ts,
    amount,
    counterparty_country
FROM synthetic_transactions
WHERE channel = 'cash_deposit'
  AND direction = 'incoming'
  AND amount >= 9000
  AND amount < 10000
ORDER BY customer_id, transaction_ts;

-- 1A. Large cash activity at or above CAD 10,000 in a 24-hour window.
SELECT
    a.customer_id,
    a.transaction_id,
    a.transaction_ts,
    SUM(b.amount) AS cash_amount_24h
FROM synthetic_transactions a
JOIN synthetic_transactions b
  ON a.customer_id = b.customer_id
 AND b.transaction_ts BETWEEN a.transaction_ts - INTERVAL '1' DAY AND a.transaction_ts
WHERE b.channel = 'cash_deposit'
  AND b.direction = 'incoming'
GROUP BY a.customer_id, a.transaction_id, a.transaction_ts
HAVING SUM(b.amount) >= 10000
ORDER BY cash_amount_24h DESC;

-- 2. Customers with repeated near-threshold cash deposits within 7 days.
SELECT
    a.customer_id,
    a.transaction_id,
    a.transaction_ts,
    COUNT(b.transaction_id) AS near_threshold_cash_count_7d,
    SUM(b.amount) AS near_threshold_cash_amount_7d
FROM synthetic_transactions a
JOIN synthetic_transactions b
  ON a.customer_id = b.customer_id
 AND b.transaction_ts BETWEEN a.transaction_ts - INTERVAL '7' DAY AND a.transaction_ts
WHERE b.channel = 'cash_deposit'
  AND b.direction = 'incoming'
  AND b.amount >= 9000
  AND b.amount < 10000
GROUP BY a.customer_id, a.transaction_id, a.transaction_ts
HAVING COUNT(b.transaction_id) >= 3
ORDER BY near_threshold_cash_count_7d DESC, near_threshold_cash_amount_7d DESC;

-- 3. Wire transactions involving high-risk jurisdictions.
SELECT
    transaction_id,
    customer_id,
    transaction_ts,
    direction,
    amount,
    counterparty_country
FROM synthetic_transactions
WHERE channel = 'wire'
  AND counterparty_country IN ('IR', 'KP', 'SY', 'MM', 'AF', 'RU', 'VE')
ORDER BY amount DESC;

-- 4. Rapid movement of funds: outgoing wire soon after incoming transaction.
SELECT
    out_tx.customer_id,
    in_tx.transaction_id AS incoming_transaction_id,
    out_tx.transaction_id AS outgoing_transaction_id,
    in_tx.transaction_ts AS incoming_ts,
    out_tx.transaction_ts AS outgoing_ts,
    in_tx.amount AS incoming_amount,
    out_tx.amount AS outgoing_amount,
    out_tx.counterparty_country AS outgoing_country
FROM synthetic_transactions out_tx
JOIN synthetic_transactions in_tx
  ON out_tx.customer_id = in_tx.customer_id
 AND in_tx.direction = 'incoming'
 AND in_tx.transaction_ts < out_tx.transaction_ts
 AND in_tx.transaction_ts >= out_tx.transaction_ts - INTERVAL '3' DAY
WHERE out_tx.direction = 'outgoing'
  AND out_tx.channel = 'wire'
  AND in_tx.amount >= out_tx.amount * 0.75
ORDER BY out_tx.customer_id, out_tx.transaction_ts;

-- 5. Top customer cases by scored risk output.
SELECT
    customer_id,
    MAX(risk_score) AS max_risk_score,
    AVG(risk_score) AS avg_risk_score,
    SUM(CASE WHEN risk_band = 'High' THEN 1 ELSE 0 END) AS high_alert_count,
    SUM(amount) AS total_amount
FROM scored_transactions
GROUP BY customer_id
HAVING SUM(CASE WHEN risk_band = 'High' THEN 1 ELSE 0 END) > 0
ORDER BY high_alert_count DESC, max_risk_score DESC, total_amount DESC;

-- 5A. EDD queue for high-risk customers and transactions.
SELECT
    customer_id,
    transaction_id,
    transaction_ts,
    risk_score,
    risk_band,
    base_risk_rating,
    amount,
    counterparty_country,
    alert_reasons
FROM scored_transactions
WHERE edd_recommended = TRUE
ORDER BY risk_score DESC, transaction_ts;

-- 5B. STR review candidates requiring investigator assessment.
SELECT
    customer_id,
    transaction_id,
    transaction_ts,
    risk_score,
    amount,
    channel,
    direction,
    counterparty_country,
    alert_reasons
FROM scored_transactions
WHERE str_review_recommended = TRUE
ORDER BY risk_score DESC, amount DESC;

-- 6. Alert quality review by synthetic label.
SELECT
    risk_band,
    label_suspicious,
    COUNT(*) AS transaction_count,
    AVG(risk_score) AS avg_risk_score
FROM scored_transactions
GROUP BY risk_band, label_suspicious
ORDER BY risk_band, label_suspicious;
