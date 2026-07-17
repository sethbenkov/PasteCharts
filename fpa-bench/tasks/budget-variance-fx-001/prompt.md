# Opex variance: FX vs organic

International departments budget in local currency. Finance reports in USD. Split the total
USD opex variance into an FX component and an organic (constant-currency) component.

{data}

Conventions:

- Budget USD = budget_local x budget_fx_rate_to_usd; Actual USD = actual_local x actual_fx_rate_to_usd.
- Total variance (USD) = total actual USD - total budget USD. Positive = overspend.
- **FX variance** = sum over departments of actual_local x (actual_rate - budget_rate).
- **Organic variance** = sum over departments of (actual_local - budget_local) x budget_rate.
- FX + organic must equal the total variance exactly.
- `largest_organic_overspend_dept` = the department with the largest organic variance in USD
  (most over budget on a constant-currency basis). Use the exact department name from the data.

Report: `total_budget_usd`, `total_actual_usd`, `total_variance_usd`, `fx_variance_usd`,
`organic_variance_usd`, `largest_organic_overspend_dept`.
