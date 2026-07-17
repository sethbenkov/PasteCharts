# Cohort revenue retention

Below is a raw transaction extract (one row per customer per active month, 2025).
Build monthly revenue cohorts and compute retention.

{data}

Definitions:

- A customer's **cohort** is the calendar month of their first transaction.
- Cohort revenue at month offset k = total revenue in the cohort's (first month + k) from
  customers belonging to that cohort. Offset 0 is the cohort's first month.
- **Mk revenue retention %** = cohort revenue at offset k / cohort revenue at offset 0 x 100.

Report:
- `jan_cohort_customers` — number of distinct customers in the 2025-01 cohort
- `jan_cohort_month0_revenue` — 2025-01 cohort revenue at offset 0
- `jan_cohort_m3_retention_pct`, `jan_cohort_m6_retention_pct`
- `apr_cohort_m3_retention_pct` — for the 2025-04 cohort
- `best_m3_retention_cohort` — which cohort (format `YYYY-MM`, among 2025-01 through 2025-06)
  has the highest M3 revenue retention
