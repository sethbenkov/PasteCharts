# FY2025 SaaS metrics

Compute the company's FY2025 SaaS metrics from the monthly MRR movement ledger below.
Contraction and churn are recorded as **negative** numbers.

{data}

Definitions (use exactly these):

- Ending MRR = beginning MRR (Jan 1) + sum of all monthly movements (new + expansion + contraction + churn).
- Ending ARR = ending MRR x 12. ARR growth % = (ending MRR / beginning MRR - 1) x 100.
- **NDR %** (full-year, beginning-of-period basis) = (beginning MRR + total expansion + total
  contraction + total churn) / beginning MRR x 100. New-business MRR is excluded.
- **GRR %** = (beginning MRR + total contraction + total churn) / beginning MRR x 100.
- Blended CAC = total FY2025 S&M spend / total new customers added in FY2025.
- CAC payback (months) = blended CAC / (average new-customer MRR x gross margin), where
  average new-customer MRR = total new MRR / total new customers, and gross margin is the
  `gross_margin_pct` parameter as a fraction.
- Rule of 40 score = ARR growth % + FY2025 EBITDA margin % (given as a parameter).

Report: `ending_mrr`, `ending_arr`, `arr_growth_pct`, `ndr_pct`, `grr_pct`, `blended_cac`,
`cac_payback_months`, `rule_of_40_score`.
