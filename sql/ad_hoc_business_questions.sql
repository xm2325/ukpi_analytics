-- Ad hoc business questions for the UKPI synthetic analytics mart.
-- These are examples of questions a stakeholder might ask.

-- 1. Which segments have the highest cash ratio?
SELECT
    segment,
    COUNT(*) AS n_customers,
    AVG(cash_ratio) AS mean_cash_ratio,
    AVG(aum) AS mean_aum
FROM customer_segments
GROUP BY segment
ORDER BY mean_cash_ratio DESC;

-- 2. Which high-AUM customers are not digitally active?
SELECT
    customer_id,
    segment,
    aum,
    cash_ratio,
    active_days_6m
FROM customer_segments
WHERE aum >= (
    SELECT percentile_90 FROM executive_metrics WHERE metric = 'aum'
)
AND active_days_6m < 10
ORDER BY aum DESC
LIMIT 50;

-- 3. Which offer has the best treatment-control lift in each segment?
WITH ranked AS (
    SELECT
        segment,
        offer_type,
        treatment_conversion_rate,
        control_conversion_rate,
        absolute_uplift,
        ROW_NUMBER() OVER (
            PARTITION BY segment
            ORDER BY absolute_uplift DESC
        ) AS rn
    FROM offer_uplift_by_segment
)
SELECT *
FROM ranked
WHERE rn = 1
ORDER BY absolute_uplift DESC;

-- 4. Which customers look suitable for neutral cash education?
SELECT
    customer_id,
    segment,
    aum,
    cash_balance,
    cash_ratio,
    active_days_6m
FROM customer_segments
WHERE cash_ratio >= 0.30
AND cash_balance >= 10000
ORDER BY cash_balance DESC
LIMIT 100;

-- 5. Which pension customers have low recent contribution activity?
SELECT
    customer_id,
    segment,
    age,
    aum,
    contribution_18m,
    active_days_6m
FROM customer_segments
WHERE has_sipp = 1
AND age >= 45
AND contribution_18m < 500
ORDER BY age DESC, aum DESC
LIMIT 100;

-- 6. How do treatment and control conversion rates compare by offer?
SELECT
    offer_type,
    assigned_group,
    COUNT(*) AS n_events,
    AVG(converted) AS conversion_rate
FROM campaign_events_with_segments
GROUP BY offer_type, assigned_group
ORDER BY offer_type, assigned_group;
