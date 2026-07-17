# Working capital diagnostics

Compute the company's working capital cycle from average balances, and size the cash that a
collections initiative would free up.

{data}

Conventions (365-day year, average balances):

- DSO = avg AR / revenue x 365. DIO = avg inventory / COGS x 365. DPO = avg AP / COGS x 365.
- Cash conversion cycle = DSO + DIO - DPO.
- Cash freed by the DSO improvement = (improvement days / 365) x revenue.

Report: `dso_days`, `dio_days`, `dpo_days`, `cash_conversion_cycle_days`,
`cash_freed_by_dso_improvement`.
