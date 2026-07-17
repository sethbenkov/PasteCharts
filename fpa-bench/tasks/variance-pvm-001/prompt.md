# Revenue variance decomposition (price / volume / mix)

You are a senior FP&A analyst. Q3 revenue came in different from budget and the CFO wants
the variance decomposed into price, volume, and mix effects by end of day.

{data}

Use exactly these conventions (per-product, budget-weighted):

- Let `AQ_i`, `AP_i` be actual units and actual price for product i; `BQ_i`, `BP_i` the budget values.
- `AQ_tot = sum(AQ_i)`, `BQ_tot = sum(BQ_i)`, and the budget average price
  `P_bar = (sum of BQ_i * BP_i) / BQ_tot`.
- **Price variance** = sum over i of `(AP_i - BP_i) * AQ_i`
- **Volume variance** = `(AQ_tot - BQ_tot) * P_bar`
- **Mix variance** = sum over i of `(AQ_i - AQ_tot * (BQ_i / BQ_tot)) * BP_i`

These three components must sum exactly to the total revenue variance (actual revenue - budget revenue).

Report these fields (all in dollars):
- `budget_revenue`
- `actual_revenue`
- `total_revenue_variance`
- `price_variance`
- `volume_variance`
- `mix_variance`
