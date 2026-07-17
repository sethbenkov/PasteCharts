"""Independent verification of every task's answer key.

Each solver here re-derives the answers ONLY from the CSVs on disk — deliberately written
separately from bench/generators.py — so a bug in a generator's answer math gets caught as a
mismatch. Also asserts the structural invariants (variance bridges tie, balance sheet balances).
"""

import csv
import json
import math
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def read_csv(task, name):
    with (TASKS / task / "data" / name).open() as fh:
        return list(csv.DictReader(fh))


def key(task):
    return json.loads((TASKS / task / "answer_key.json").read_text())


def close(a, b, rel=1e-6, abs_=1e-4):
    assert math.isclose(a, b, rel_tol=rel, abs_tol=abs_), f"{a} != {b}"


def test_variance_pvm():
    rows = read_csv("variance-pvm-001", "budget_vs_actual.csv")
    k = key("variance-pvm-001")
    b_rev = sum(float(r["budget_units"]) * float(r["budget_price"]) for r in rows)
    a_rev = sum(float(r["actual_units"]) * float(r["actual_price"]) for r in rows)
    bq = sum(float(r["budget_units"]) for r in rows)
    aq = sum(float(r["actual_units"]) for r in rows)
    pbar = b_rev / bq
    price = sum((float(r["actual_price"]) - float(r["budget_price"])) * float(r["actual_units"]) for r in rows)
    volume = (aq - bq) * pbar
    mix = sum((float(r["actual_units"]) - aq * float(r["budget_units"]) / bq) * float(r["budget_price"]) for r in rows)
    close(k["budget_revenue"], b_rev)
    close(k["actual_revenue"], a_rev)
    close(k["price_variance"], price)
    close(k["volume_variance"], volume)
    close(k["mix_variance"], mix)
    # invariant: bridge ties
    close(price + volume + mix, a_rev - b_rev)
    close(k["total_revenue_variance"], a_rev - b_rev)


def test_three_statement():
    a = {r["assumption"]: float(r["value"]) for r in read_csv("three-statement-001", "assumptions.csv")}
    p = {r["line_item"]: float(r["value"]) for r in read_csv("three-statement-001", "prior_balance_sheet.csv")}
    k = key("three-statement-001")
    rev = a["prior_year_revenue"] * (1 + a["revenue_growth_pct"] / 100)
    cogs = rev * a["cogs_pct_of_revenue"] / 100
    gross = rev - cogs
    opex = a["opex_fixed"] + rev * a["opex_variable_pct_of_revenue"] / 100
    ebitda = gross - opex
    ebit = ebitda - a["depreciation"]
    interest = p["long_term_debt"] * a["interest_rate_pct_on_beginning_debt"] / 100
    pretax = ebit - interest
    ni = pretax - max(0, pretax) * a["tax_rate_pct"] / 100
    ar = a["dso_days"] / 365 * rev
    inv = a["dio_days"] / 365 * cogs
    ap = a["dpo_days"] / 365 * cogs
    d_nwc = (ar + inv - ap) - (p["accounts_receivable"] + p["inventory"] - p["accounts_payable"])
    cash = p["cash"] + ni + a["depreciation"] - d_nwc - a["capex"] - a["debt_repayment"]
    ppe = p["net_ppe"] + a["capex"] - a["depreciation"]
    re = p["retained_earnings"] + ni
    assets = cash + ar + inv + ppe
    close(k["revenue"], rev)
    close(k["gross_profit"], gross)
    close(k["ebitda"], ebitda)
    close(k["net_income"], ni, abs_=0.01)
    close(k["change_in_net_working_capital"], d_nwc, abs_=0.01)
    close(k["ending_cash"], cash, abs_=0.01)
    close(k["ending_net_ppe"], ppe)
    close(k["ending_retained_earnings"], re, abs_=0.01)
    close(k["ending_total_assets"], assets, abs_=0.02)
    # invariant: balance sheet balances
    liab_eq = ap + (p["long_term_debt"] - a["debt_repayment"]) + p["common_stock"] + re
    close(assets, liab_eq, abs_=0.02)


def test_thirteen_week_cash():
    ar = read_csv("thirteen-week-cash-001", "ar_collections.csv")
    ap = read_csv("thirteen-week-cash-001", "ap_disbursements.csv")
    rec = read_csv("thirteen-week-cash-001", "recurring_disbursements.csv")
    params = {r["parameter"]: float(r["value"]) for r in read_csv("thirteen-week-cash-001", "parameters.csv")}
    k = key("thirteen-week-cash-001")
    inflow = {w: 0.0 for w in range(1, 14)}
    outflow = {w: 0.0 for w in range(1, 14)}
    for r in ar:
        inflow[int(r["expected_collection_week"])] += float(r["amount"])
    for r in ap:
        outflow[int(r["due_week"])] += float(r["amount"])
    for r in rec:
        for w in r["weeks"].split(";"):
            outflow[int(w)] += float(r["amount_per_occurrence"])
    cash, ending = params["opening_cash"], {}
    for w in range(1, 14):
        cash += inflow[w] - outflow[w]
        ending[w] = cash
    close(k["total_collections"], sum(inflow.values()))
    close(k["total_disbursements"], sum(outflow.values()))
    close(k["ending_cash_week_13"], ending[13], abs_=0.02)
    mn = min(ending.values())
    close(k["minimum_ending_cash"], mn, abs_=0.02)
    assert ending[k["minimum_cash_week"]] == mn
    assert k["weeks_below_covenant"] == sum(1 for v in ending.values() if v < params["minimum_cash_covenant"])


def test_saas_metrics():
    rows = read_csv("saas-metrics-001", "mrr_movements.csv")
    cust = read_csv("saas-metrics-001", "customer_movements.csv")
    sm = read_csv("saas-metrics-001", "sales_marketing_spend.csv")
    params = {r["parameter"]: float(r["value"]) for r in read_csv("saas-metrics-001", "parameters.csv")}
    k = key("saas-metrics-001")
    bop = params["beginning_mrr_jan1"]
    new = sum(float(r["new_mrr"]) for r in rows)
    exp = sum(float(r["expansion_mrr"]) for r in rows)
    con = sum(float(r["contraction_mrr"]) for r in rows)
    chn = sum(float(r["churned_mrr"]) for r in rows)
    assert con < 0 and chn < 0, "contraction/churn must be stored as negatives"
    eop = bop + new + exp + con + chn
    close(k["ending_mrr"], eop, abs_=0.02)
    close(k["ending_arr"], eop * 12, abs_=0.25)
    close(k["ndr_pct"], (bop + exp + con + chn) / bop * 100)
    close(k["grr_pct"], (bop + con + chn) / bop * 100)
    total_sm = sum(float(r["spend"]) for r in sm)
    new_c = sum(int(r["new_customers"]) for r in cust)
    cac = total_sm / new_c
    close(k["blended_cac"], cac)
    close(k["cac_payback_months"], cac / ((new / new_c) * params["gross_margin_pct"] / 100))
    growth = (eop / bop - 1) * 100
    close(k["arr_growth_pct"], growth, abs_=0.001)
    close(k["rule_of_40_score"], growth + params["fy2025_ebitda_margin_pct"], abs_=0.001)


def test_cohort_retention():
    rows = read_csv("cohort-retention-001", "transactions.csv")
    k = key("cohort-retention-001")
    first = {}
    for r in rows:
        c = r["customer_id"]
        if c not in first or r["month"] < first[c]:
            first[c] = r["month"]
    cohort_rev = {}
    for r in rows:
        cm = first[r["customer_id"]]
        offset = (int(r["month"][:4]) - int(cm[:4])) * 12 + int(r["month"][5:]) - int(cm[5:])
        cohort_rev.setdefault(cm, {}).setdefault(offset, 0.0)
        cohort_rev[cm][offset] += float(r["revenue"])

    def ret(cm, kk):
        return cohort_rev[cm].get(kk, 0.0) / cohort_rev[cm][0] * 100

    assert k["jan_cohort_customers"] == sum(1 for c, m in first.items() if m == "2025-01")
    close(k["jan_cohort_month0_revenue"], cohort_rev["2025-01"][0])
    close(k["jan_cohort_m3_retention_pct"], ret("2025-01", 3))
    close(k["jan_cohort_m6_retention_pct"], ret("2025-01", 6))
    close(k["apr_cohort_m3_retention_pct"], ret("2025-04", 3))
    months = [f"2025-{m:02d}" for m in range(1, 7)]
    assert k["best_m3_retention_cohort"] == max(months, key=lambda cm: ret(cm, 3))


def test_budget_variance_fx():
    rows = read_csv("budget-variance-fx-001", "opex_by_department.csv")
    k = key("budget-variance-fx-001")
    tb = sum(float(r["budget_local"]) * float(r["budget_fx_rate_to_usd"]) for r in rows)
    ta = sum(float(r["actual_local"]) * float(r["actual_fx_rate_to_usd"]) for r in rows)
    fx = sum(float(r["actual_local"]) * (float(r["actual_fx_rate_to_usd"]) - float(r["budget_fx_rate_to_usd"])) for r in rows)
    org = sum((float(r["actual_local"]) - float(r["budget_local"])) * float(r["budget_fx_rate_to_usd"]) for r in rows)
    close(k["total_budget_usd"], tb)
    close(k["total_actual_usd"], ta)
    close(k["total_variance_usd"], ta - tb)
    close(k["fx_variance_usd"], fx)
    close(k["organic_variance_usd"], org)
    close(fx + org, ta - tb)  # invariant: split ties to total
    worst = max(rows, key=lambda r: (float(r["actual_local"]) - float(r["budget_local"])) * float(r["budget_fx_rate_to_usd"]))
    assert k["largest_organic_overspend_dept"] == worst["department"]


def test_capital_allocation():
    cap = {r["parameter"]: float(r["value"]) for r in read_csv("capital-allocation-001", "capital_structure.csv")}
    cf_rows = read_csv("capital-allocation-001", "project_cash_flows.csv")
    k = key("capital-allocation-001")
    cfs_a = [float(r["project_a"]) for r in cf_rows]
    cfs_b = [float(r["project_b"]) for r in cf_rows]
    ke = cap["risk_free_rate_pct"] + cap["equity_beta"] * cap["equity_risk_premium_pct"]
    kd = cap["pretax_cost_of_debt_pct"] * (1 - cap["tax_rate_pct"] / 100)
    tot = cap["market_value_of_debt"] + cap["market_value_of_equity"]
    wacc = cap["market_value_of_equity"] / tot * ke + cap["market_value_of_debt"] / tot * kd
    close(k["wacc_pct"], wacc, abs_=0.001)
    r = wacc / 100

    def npv(cfs, rate):
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(cfs))

    close(k["npv_project_a"], npv(cfs_a, r), abs_=0.02)
    close(k["npv_project_b"], npv(cfs_b, r), abs_=0.02)
    # IRR keys should drive project NPV to ~0
    assert abs(npv(cfs_a, k["irr_project_a_pct"] / 100)) < abs(cfs_a[0]) * 1e-3
    assert abs(npv(cfs_b, k["irr_project_b_pct"] / 100)) < abs(cfs_b[0]) * 1e-3
    # payback: cumulative at floor(payback) is <= 0, next year covers it
    pb = k["payback_years_project_a"]
    whole = int(pb)
    cum = sum(cfs_a[: whole + 1])
    assert cum <= 1e-6
    close(pb, whole + (-cum) / cfs_a[whole + 1], abs_=0.01)
    assert k["recommended_project"] == ("A" if npv(cfs_a, r) >= npv(cfs_b, r) else "B")


def test_unit_economics():
    rows = read_csv("unit-economics-001", "channels.csv")
    params = {r["parameter"]: float(r["value"]) for r in read_csv("unit-economics-001", "parameters.csv")}
    k = key("unit-economics-001")
    enriched = []
    for r in rows:
        cac = float(r["cac"])
        contrib = float(r["avg_order_value"]) * float(r["gross_margin_pct"]) / 100 - float(r["fulfillment_cost_per_order"]) - cac
        enriched.append((r["channel"], cac, int(r["max_monthly_orders"]), contrib, contrib / cac))
    best = max(enriched, key=lambda e: e[4])
    assert k["best_channel_by_contribution_per_cac_dollar"] == best[0]
    close(k["best_channel_contribution_per_order"], best[3])
    remaining, orders_tot, contrib_tot = params["monthly_marketing_budget"], 0, 0.0
    for name, cac, cap, contrib, roi in sorted(enriched, key=lambda e: -e[4]):
        if contrib <= 0 or remaining <= 0:
            continue
        n = min(cap, int(remaining // cac))
        remaining -= n * cac
        orders_tot += n
        contrib_tot += n * contrib
    assert k["optimal_total_orders"] == orders_tot
    close(k["optimal_total_contribution"], contrib_tot, abs_=0.02)
    close(k["unspent_budget"], remaining, abs_=0.02)


def test_working_capital():
    f = {r["line_item"]: float(r["value"]) for r in read_csv("working-capital-001", "financials.csv")}
    k = key("working-capital-001")
    dso = f["avg_accounts_receivable"] / f["fy_revenue"] * 365
    dio = f["avg_inventory"] / f["fy_cogs"] * 365
    dpo = f["avg_accounts_payable"] / f["fy_cogs"] * 365
    close(k["dso_days"], dso)
    close(k["dio_days"], dio)
    close(k["dpo_days"], dpo)
    close(k["cash_conversion_cycle_days"], dso + dio - dpo)
    close(k["cash_freed_by_dso_improvement"], f["dso_improvement_days"] / 365 * f["fy_revenue"])


def test_forecast_revrec():
    cap = {r["parameter"]: float(r["value"]) for r in read_csv("forecast-revrec-001", "sales_capacity.csv")}
    ramp_rows = read_csv("forecast-revrec-001", "ramp_and_seasonality.csv")
    prior = {r["quarter"]: float(r["bookings"]) for r in read_csv("forecast-revrec-001", "prior_bookings.csv")}
    k = key("forecast-revrec-001")
    ramp = [float(r["ramp_productivity_pct"]) / 100 for r in ramp_rows]
    seas = [float(r["seasonality_multiplier"]) for r in ramp_rows]
    hires = [int(cap[f"new_hires_q{q}_2026"]) for q in range(1, 5)]
    quota = cap["quarterly_quota_fully_ramped"]
    bookings = []
    for q in range(4):
        capacity = cap["fully_ramped_reps_at_jan1_2026"]
        for hq in range(q + 1):
            capacity += hires[hq] * ramp[q - hq]
        bookings.append(capacity * quota * seas[q])
    for q in range(4):
        close(k[f"bookings_2026_q{q+1}"], bookings[q], abs_=0.02)
    close(k["total_bookings_2026"], sum(bookings), abs_=0.05)
    all_b = [prior["2025-Q2"], prior["2025-Q3"], prior["2025-Q4"]] + bookings
    for q in range(4):
        idx = q + 3
        rev = sum(all_b[j] / 4 for j in range(max(0, idx - 3), idx + 1))
        close(k[f"revenue_2026_q{q+1}"], rev, abs_=0.05)


def test_error_detection():
    pnl = {r["line_item"]: float(r["value"]) for r in read_csv("error-detection-001", "reported_pnl.csv")}
    k = key("error-detection-001")
    gross = pnl["revenue"] - pnl["cogs"]
    opex = pnl["sales_and_marketing"] + pnl["research_and_development"] + pnl["general_and_administrative"]
    op_inc = gross - opex - pnl["depreciation"]
    pretax = op_inc - pnl["interest_expense"]
    tax = round(max(0, pretax) * pnl["tax_rate_pct"] / 100)
    close(k["correct_gross_profit"], gross)
    close(k["correct_total_operating_expenses"], opex)
    close(k["correct_operating_income"], op_inc)
    close(k["correct_pretax_income"], pretax)
    close(k["correct_tax_expense"], tax)
    close(k["correct_net_income"], pretax - tax)
    # the injected errors must actually be wrong (task isn't trivially a copy job)
    assert abs(pnl["gross_profit"] - gross) > 1
    assert abs(pnl["net_income"] - (pretax - tax)) > 1


def test_board_memo_key_consistency():
    rev = read_csv("board-memo-001", "revenue_by_region.csv")
    opex = read_csv("board-memo-001", "opex_by_department.csv")
    k = key("board-memo-001")
    tb = sum(float(r["budget_q3"]) for r in rev)
    ta = sum(float(r["actual_q3"]) for r in rev)
    assert k["total_revenue_budget"] == tb
    assert k["total_revenue_actual"] == ta
    assert k["revenue_variance"] == ta - tb
    ob = sum(float(r["budget_q3"]) for r in opex)
    oa = sum(float(r["actual_q3"]) for r in opex)
    assert k["opex_variance_favorable"] == ob - oa
    # the intended story must hold in the data: EMEA is the miss, opex is favorable
    emea = next(r for r in rev if r["region"] == "EMEA")
    assert float(emea["actual_q3"]) < float(emea["budget_q3"]) * 0.9
    assert oa < ob


def test_every_numeric_task_key_covers_all_graded_fields():
    for d in sorted(TASKS.iterdir()):
        meta = json.loads((d / "task.json").read_text())
        if meta.get("grading") != "numeric":
            continue
        k = json.loads((d / "answer_key.json").read_text())
        for f in meta["fields"]:
            assert f["name"] in k, f"{d.name}: field {f['name']} missing from answer key"
