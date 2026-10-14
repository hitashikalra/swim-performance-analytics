-- Monthly pace by stroke and distance, plus change since the first month.
-- Uses the best swim each month rather than the average, since practice
-- logs mix easy and hard efforts.

WITH monthly AS (
    SELECT
        stroke,
        distance_m,
        substr(swim_date, 1, 7)  AS month,
        MIN(pace_per_100m)       AS best_pace,
        ROUND(AVG(pace_per_100m), 2) AS avg_pace,
        COUNT(*)                 AS swims
    FROM swims
    GROUP BY stroke, distance_m, month
),

with_baseline AS (
    SELECT
        *,
        FIRST_VALUE(best_pace) OVER (
            PARTITION BY stroke, distance_m ORDER BY month
        ) AS first_month_best,
        LAG(best_pace) OVER (
            PARTITION BY stroke, distance_m ORDER BY month
        ) AS prev_month_best
    FROM monthly
)

SELECT
    stroke,
    distance_m,
    month,
    swims,
    best_pace,
    avg_pace,
    ROUND((best_pace - prev_month_best) / prev_month_best * 100, 2)   AS pct_change_vs_prev_month,
    ROUND((best_pace - first_month_best) / first_month_best * 100, 2) AS pct_change_since_start
FROM with_baseline
ORDER BY stroke, distance_m, month;
