# P&L review: find the errors

An intern produced the P&L below and several **subtotals** are wrong. The individual component
lines (revenue, cogs, the three opex lines, depreciation, interest_expense, and tax_rate_pct)
are correct and authoritative. Recompute every subtotal from the components. All figures in
$ thousands.

{data}

Conventions:

- gross_profit = revenue - cogs
- total_operating_expenses = sales_and_marketing + research_and_development + general_and_administrative
  (depreciation is presented separately, not part of this subtotal)
- operating_income = gross_profit - total_operating_expenses - depreciation
- pretax_income = operating_income - interest_expense
- tax_expense = tax_rate_pct x pretax_income (rounded to the nearest whole number; zero if pretax
  income is negative)
- net_income = pretax_income - tax_expense

Report the corrected values: `correct_gross_profit`, `correct_total_operating_expenses`,
`correct_operating_income`, `correct_pretax_income`, `correct_tax_expense`, `correct_net_income`.
