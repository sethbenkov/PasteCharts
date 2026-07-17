# Marketing budget allocation by unit economics

Allocate next month's marketing budget across acquisition channels to maximize total
contribution profit.

{data}

Conventions:

- Contribution per order (net of CAC) = avg_order_value x gross_margin_pct - fulfillment_cost_per_order - cac.
- Rank channels by contribution per CAC dollar = contribution per order / cac.
- Allocate greedily: fund channels in descending contribution-per-CAC-dollar order. In each
  channel buy `orders = min(max_monthly_orders, floor(remaining_budget / cac))` orders, spending
  `orders x cac`. Skip channels whose contribution per order is zero or negative. Continue until
  the budget or channels run out.
- `unspent_budget` = budget remaining after the allocation above.

Report: `best_channel_by_contribution_per_cac_dollar` (exact channel name),
`best_channel_contribution_per_order`, `optimal_total_orders`, `optimal_total_contribution`,
`unspent_budget`.
