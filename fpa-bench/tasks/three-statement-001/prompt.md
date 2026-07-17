# Linked three-statement projection (FY2026)

Build a one-year integrated P&L / balance sheet / cash flow projection for FY2026
from the prior-year (FY2025) balance sheet and the assumptions below. All figures in $ thousands.

{data}

Modeling conventions (follow exactly):

- Revenue = prior-year revenue x (1 + growth). COGS = % of revenue. Opex = fixed + variable % of revenue
  (opex excludes depreciation).
- EBITDA = revenue - COGS - opex. EBIT = EBITDA - depreciation.
- Interest expense = rate x **beginning** (FY2025 ending) debt balance. No interest income.
- Tax = tax rate x pretax income (if pretax income is positive; else zero). Net income = pretax - tax.
- Working capital: AR = DSO/365 x revenue; Inventory = DIO/365 x COGS; AP = DPO/365 x COGS.
  Change in NWC = (AR + Inventory - AP) at FY2026 end minus the same at FY2025 end.
  Use 365 days.
- Cash flow: ending cash = beginning cash + net income + depreciation - change in NWC - capex - debt repayment.
- Net PP&E = prior + capex - depreciation. Retained earnings = prior + net income (no dividends).
  Debt = prior - repayment. Common stock unchanged.
- The balance sheet must balance; use that as a self-check.

Report these fields ($ thousands):
`revenue`, `gross_profit`, `ebitda`, `net_income`, `change_in_net_working_capital`
(positive = NWC increased), `ending_cash`, `ending_net_ppe`, `ending_retained_earnings`,
`ending_total_assets`.
