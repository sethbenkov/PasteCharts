# 13-week cash flow forecast

You are the treasury analyst for a company on a tight cash position. Build a 13-week direct
cash flow forecast (weeks 1 through 13) and check it against the revolver's minimum-cash covenant.

{data}

Conventions:

- Cash inflows: each AR invoice is collected in full in its `expected_collection_week`.
- Cash outflows: each AP bill is paid in full in its `due_week`. Each recurring item is paid at
  `amount_per_occurrence` in each week listed in its semicolon-separated `weeks` column.
- Ending cash for week w = ending cash for week w-1 + inflows(w) - outflows(w); week 1 starts
  from `opening_cash`.
- `weeks_below_covenant` = number of weeks (out of 13) whose **ending** cash is strictly below
  `minimum_cash_covenant`.

Report: `total_collections`, `total_disbursements` (both over the full 13 weeks),
`ending_cash_week_13`, `minimum_ending_cash` (the lowest weekly ending cash),
`minimum_cash_week` (the week number it occurs, 1-13), `weeks_below_covenant`.
