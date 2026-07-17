# FY2026 bookings and revenue forecast

Build a driver-based FY2026 forecast: sales-capacity-driven bookings, then ratable revenue
recognition.

{data}

Conventions:

- **Capacity**: a fully-ramped rep produces 1.0 x quarterly quota. New hires start at the
  beginning of their hire quarter and follow the ramp schedule by quarter of tenure (quarter of
  tenure 1 = their hire quarter). Reps listed as fully ramped at Jan 1 2026 produce 100% all year.
  No attrition.
- **Bookings** for fiscal quarter q = (sum of all reps' ramp-weighted capacity in q) x quota x
  that fiscal quarter's seasonality multiplier. Note the ramp table's first column serves double
  duty: rows 1-4 give both the ramp % for tenure-quarter 1-4 and the seasonality multiplier for
  fiscal Q1-Q4 2026.
- **Revenue**: all bookings are 12-month contracts recognized ratably over 4 quarters **starting
  in the quarter booked** (a quarter's revenue = 1/4 of each of the current and prior 3 quarters'
  bookings). Prior-year (2025 Q2-Q4) bookings are provided for the recognition tail; assume
  2025-Q1 and earlier contribute nothing to 2026 revenue.

Report: `bookings_2026_q1` .. `bookings_2026_q4`, `total_bookings_2026`,
`revenue_2026_q1` .. `revenue_2026_q4`, `total_revenue_2026`.
