# Capital allocation: pick a project

The company can fund one of two projects. Compute the WACC from the capital structure, then
NPV (at WACC), IRR, and simple payback, and recommend a project.

{data}

Conventions:

- Cost of equity (CAPM): risk-free rate + beta x equity risk premium.
- After-tax cost of debt = pretax cost of debt x (1 - tax rate).
- WACC = E/(D+E) x cost of equity + D/(D+E) x after-tax cost of debt, using market values.
- NPV discounts each year-t cash flow at WACC: CF_t / (1 + WACC)^t, year 0 undiscounted.
- IRR = rate where NPV is zero (report as a percentage).
- Simple payback (undiscounted, fractional): the year count where cumulative cash flow crosses
  zero, interpolating within the crossing year. E.g. if cumulative is -100 after year 2 and the
  year-3 cash flow is 400, payback = 2.25.
- Recommend the project with the higher NPV at WACC. Answer "A" or "B".

Report: `wacc_pct`, `npv_project_a`, `npv_project_b`, `irr_project_a_pct`, `irr_project_b_pct`,
`payback_years_project_a`, `recommended_project`.
