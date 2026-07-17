"""Seeded synthetic data generators.

Every quantitative task's data AND answer key are produced here, by code.
Ground truth is computed from the data exactly as written to disk (post-rounding),
so the answer key is always consistent with what the model sees. Regenerating
with a different seed produces a fresh, uncontaminated instance of the benchmark.

Usage: python -m bench generate [--seed 42] [--task <task_id>]
"""

from __future__ import annotations

import csv
import json
import random
import zlib
from pathlib import Path

from .schema import TASKS_DIR

GENERATORS = {}


def generator(task_id):
    def deco(fn):
        GENERATORS[task_id] = fn
        return fn
    return deco


def _write_csv(task_id: str, name: str, header: list[str], rows: list[list]):
    d = TASKS_DIR / task_id / "data"
    d.mkdir(parents=True, exist_ok=True)
    with (d / name).open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _write_key(task_id: str, key: dict):
    rounded = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in key.items()}
    (TASKS_DIR / task_id / "answer_key.json").write_text(json.dumps(rounded, indent=2) + "\n")


def m2(x: float) -> float:
    """Round to cents."""
    return round(x, 2)


# ---------------------------------------------------------------------------
@generator("variance-pvm-001")
def gen_variance_pvm(seed: int):
    rng = random.Random(seed)
    products = ["Alpha", "Bravo", "Cortex", "Delta", "Echo", "Foxtrot"]
    rows = []
    for p in products:
        bq = rng.randrange(800, 12000, 50)
        bp = m2(rng.uniform(15, 240))
        aq = max(50, int(bq * rng.uniform(0.75, 1.3)))
        ap = m2(bp * rng.uniform(0.88, 1.12))
        rows.append([p, bq, bp, aq, ap])
    _write_csv("variance-pvm-001", "budget_vs_actual.csv",
               ["product", "budget_units", "budget_price", "actual_units", "actual_price"], rows)

    bq_tot = sum(r[1] for r in rows)
    aq_tot = sum(r[3] for r in rows)
    b_rev = sum(r[1] * r[2] for r in rows)
    a_rev = sum(r[3] * r[4] for r in rows)
    avg_bp = b_rev / bq_tot
    price_var = sum((r[4] - r[2]) * r[3] for r in rows)
    volume_var = (aq_tot - bq_tot) * avg_bp
    mix_var = sum((r[3] - aq_tot * (r[1] / bq_tot)) * r[2] for r in rows)
    _write_key("variance-pvm-001", {
        "budget_revenue": b_rev,
        "actual_revenue": a_rev,
        "total_revenue_variance": a_rev - b_rev,
        "price_variance": price_var,
        "volume_variance": volume_var,
        "mix_variance": mix_var,
    })


# ---------------------------------------------------------------------------
@generator("three-statement-001")
def gen_three_statement(seed: int):
    rng = random.Random(seed)
    prior_rev = rng.randrange(40_000, 90_000, 500)  # $k
    a = {
        "revenue_growth_pct": round(rng.uniform(8, 22), 1),
        "cogs_pct_of_revenue": round(rng.uniform(35, 55), 1),
        "opex_fixed": rng.randrange(8_000, 16_000, 250),
        "opex_variable_pct_of_revenue": round(rng.uniform(8, 15), 1),
        "depreciation": rng.randrange(1_500, 4_000, 100),
        "capex": rng.randrange(2_000, 6_000, 100),
        "interest_rate_pct_on_beginning_debt": round(rng.uniform(5, 9), 2),
        "tax_rate_pct": 25.0,
        "debt_repayment": rng.randrange(1_000, 3_000, 250),
        "dso_days": rng.randrange(35, 60),
        "dio_days": rng.randrange(30, 75),
        "dpo_days": rng.randrange(30, 55),
        "prior_year_revenue": prior_rev,
    }
    # prior balance sheet (all $k), constructed to balance
    p_cash = rng.randrange(5_000, 15_000, 100)
    p_ar = m2(prior_rev * rng.uniform(0.09, 0.14))
    p_cogs = prior_rev * a["cogs_pct_of_revenue"] / 100
    p_inv = m2(p_cogs * rng.uniform(0.10, 0.18))
    p_ppe = rng.randrange(12_000, 30_000, 250)
    p_ap = m2(p_cogs * rng.uniform(0.09, 0.14))
    p_debt = rng.randrange(8_000, 20_000, 500)
    p_stock = rng.randrange(5_000, 10_000, 500)
    p_re = m2(p_cash + p_ar + p_inv + p_ppe - p_ap - p_debt - p_stock)

    _write_csv("three-statement-001", "assumptions.csv", ["assumption", "value"],
               [[k, v] for k, v in a.items()])
    _write_csv("three-statement-001", "prior_balance_sheet.csv", ["line_item", "value"], [
        ["cash", p_cash], ["accounts_receivable", p_ar], ["inventory", p_inv],
        ["net_ppe", p_ppe], ["accounts_payable", p_ap], ["long_term_debt", p_debt],
        ["common_stock", p_stock], ["retained_earnings", p_re],
    ])

    rev = prior_rev * (1 + a["revenue_growth_pct"] / 100)
    cogs = rev * a["cogs_pct_of_revenue"] / 100
    gross = rev - cogs
    opex = a["opex_fixed"] + rev * a["opex_variable_pct_of_revenue"] / 100
    ebitda = gross - opex
    ebit = ebitda - a["depreciation"]
    interest = p_debt * a["interest_rate_pct_on_beginning_debt"] / 100
    pretax = ebit - interest
    tax = max(0.0, pretax) * a["tax_rate_pct"] / 100
    ni = pretax - tax

    ar = a["dso_days"] / 365 * rev
    inv = a["dio_days"] / 365 * cogs
    ap = a["dpo_days"] / 365 * cogs
    nwc_now = ar + inv - ap
    nwc_prior = p_ar + p_inv - p_ap
    d_nwc = nwc_now - nwc_prior

    cash = p_cash + ni + a["depreciation"] - d_nwc - a["capex"] - a["debt_repayment"]
    ppe = p_ppe + a["capex"] - a["depreciation"]
    re = p_re + ni
    assets = cash + ar + inv + ppe
    _write_key("three-statement-001", {
        "revenue": rev, "gross_profit": gross, "ebitda": ebitda, "net_income": ni,
        "change_in_net_working_capital": d_nwc, "ending_cash": cash,
        "ending_net_ppe": ppe, "ending_retained_earnings": re,
        "ending_total_assets": assets,
    })


# ---------------------------------------------------------------------------
@generator("thirteen-week-cash-001")
def gen_13wk(seed: int):
    rng = random.Random(seed)
    opening = rng.randrange(400_000, 900_000, 10_000)
    covenant = rng.randrange(150_000, 300_000, 25_000)

    inv_rows = []
    for i in range(1, 41):
        wk = rng.randint(1, 13)
        inv_rows.append([f"INV-{1000+i}", m2(rng.uniform(8_000, 90_000)), wk])
    _write_csv("thirteen-week-cash-001", "ar_collections.csv",
               ["invoice_id", "amount", "expected_collection_week"], inv_rows)

    ap_rows = []
    for i in range(1, 31):
        wk = rng.randint(1, 13)
        ap_rows.append([f"BILL-{2000+i}", m2(rng.uniform(5_000, 60_000)), wk])
    _write_csv("thirteen-week-cash-001", "ap_disbursements.csv",
               ["bill_id", "amount", "due_week"], ap_rows)

    payroll = rng.randrange(90_000, 160_000, 5_000)
    rent = rng.randrange(30_000, 60_000, 5_000)
    debt_svc = rng.randrange(20_000, 45_000, 5_000)
    rec_rows = [
        ["payroll", payroll, "2;4;6;8;10;12"],
        ["rent", rent, "1;5;9;13"],
        ["debt_service", debt_svc, "4;8;12"],
    ]
    _write_csv("thirteen-week-cash-001", "recurring_disbursements.csv",
               ["item", "amount_per_occurrence", "weeks"], rec_rows)
    _write_csv("thirteen-week-cash-001", "parameters.csv", ["parameter", "value"], [
        ["opening_cash", opening], ["minimum_cash_covenant", covenant],
    ])

    inflow = {w: 0.0 for w in range(1, 14)}
    outflow = {w: 0.0 for w in range(1, 14)}
    for _, amt, wk in inv_rows:
        inflow[wk] += amt
    for _, amt, wk in ap_rows:
        outflow[wk] += amt
    for _, amt, weeks in rec_rows:
        for w in weeks.split(";"):
            outflow[int(w)] += amt

    cash = float(opening)
    ending = {}
    for w in range(1, 14):
        cash += inflow[w] - outflow[w]
        ending[w] = cash
    min_wk = min(ending, key=lambda w: ending[w])
    _write_key("thirteen-week-cash-001", {
        "total_collections": sum(inflow.values()),
        "total_disbursements": sum(outflow.values()),
        "ending_cash_week_13": ending[13],
        "minimum_ending_cash": ending[min_wk],
        "minimum_cash_week": min_wk,
        "weeks_below_covenant": sum(1 for w in ending if ending[w] < covenant),
    })


# ---------------------------------------------------------------------------
@generator("saas-metrics-001")
def gen_saas(seed: int):
    rng = random.Random(seed)
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    bop_mrr = rng.randrange(800_000, 1_500_000, 10_000)
    bop_customers = rng.randrange(400, 900, 10)

    rows, cust_rows = [], []
    mrr = float(bop_mrr)
    customers = bop_customers
    tot_new = tot_exp = tot_con = tot_chn = 0.0
    tot_new_c = 0
    sm_rows = []
    for mo in months:
        new = m2(mrr * rng.uniform(0.015, 0.035))
        exp = m2(mrr * rng.uniform(0.010, 0.025))
        con = m2(-mrr * rng.uniform(0.004, 0.012))
        chn = m2(-mrr * rng.uniform(0.008, 0.020))
        rows.append([mo, new, exp, con, chn])
        new_c = rng.randint(8, 25)
        chn_c = rng.randint(3, 12)
        cust_rows.append([mo, new_c, chn_c])
        sm_rows.append([mo, rng.randrange(120_000, 260_000, 5_000)])
        mrr += new + exp + con + chn
        customers += new_c - chn_c
        tot_new += new; tot_exp += exp; tot_con += con; tot_chn += chn
        tot_new_c += new_c

    _write_csv("saas-metrics-001", "mrr_movements.csv",
               ["month", "new_mrr", "expansion_mrr", "contraction_mrr", "churned_mrr"], rows)
    _write_csv("saas-metrics-001", "customer_movements.csv",
               ["month", "new_customers", "churned_customers"], cust_rows)
    _write_csv("saas-metrics-001", "sales_marketing_spend.csv", ["month", "spend"], sm_rows)
    gm_pct = round(rng.uniform(72, 82), 1)
    ebitda_margin_pct = round(rng.uniform(-15, 10), 1)
    _write_csv("saas-metrics-001", "parameters.csv", ["parameter", "value"], [
        ["beginning_mrr_jan1", bop_mrr],
        ["beginning_customers_jan1", bop_customers],
        ["gross_margin_pct", gm_pct],
        ["fy2025_ebitda_margin_pct", ebitda_margin_pct],
    ])

    eop_mrr = mrr
    ndr = (bop_mrr + tot_exp + tot_con + tot_chn) / bop_mrr * 100
    grr = (bop_mrr + tot_con + tot_chn) / bop_mrr * 100
    total_sm = sum(r[1] for r in sm_rows)
    cac = total_sm / tot_new_c
    arpa_new = (tot_new / tot_new_c)
    cac_payback = cac / (arpa_new * gm_pct / 100)
    arr_growth = (eop_mrr / bop_mrr - 1) * 100
    _write_key("saas-metrics-001", {
        "ending_mrr": eop_mrr,
        "ending_arr": eop_mrr * 12,
        "arr_growth_pct": arr_growth,
        "ndr_pct": ndr,
        "grr_pct": grr,
        "blended_cac": cac,
        "cac_payback_months": cac_payback,
        "rule_of_40_score": arr_growth + ebitda_margin_pct,
    })


# ---------------------------------------------------------------------------
@generator("cohort-retention-001")
def gen_cohorts(seed: int):
    rng = random.Random(seed)
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    rows = []
    cohorts: dict[str, dict[int, float]] = {}
    cohort_sizes: dict[str, int] = {}
    cid = 100
    for ci, cmonth in enumerate(months[:6]):  # cohorts Jan-Jun
        n = rng.randint(12, 22)
        cohort_sizes[cmonth] = n
        decay = rng.uniform(0.82, 0.95)
        for _ in range(n):
            cid += 1
            base = m2(rng.uniform(80, 600))
            for k, mo in enumerate(months[ci:]):
                # customer survives to month k with prob decay^k; spend varies
                if k > 0 and rng.random() > decay:
                    break
                amt = m2(base * rng.uniform(0.7, 1.3))
                rows.append([f"C{cid}", mo, amt])
                cohorts.setdefault(cmonth, {}).setdefault(k, 0.0)
                cohorts[cmonth][k] += amt
    rng.shuffle(rows)
    _write_csv("cohort-retention-001", "transactions.csv",
               ["customer_id", "month", "revenue"], rows)

    def ret(cm: str, k: int) -> float:
        c = cohorts[cm]
        return c.get(k, 0.0) / c[0] * 100

    m3 = {cm: ret(cm, 3) for cm in months[:6]}
    best = max(m3, key=lambda cm: m3[cm])
    _write_key("cohort-retention-001", {
        "jan_cohort_customers": cohort_sizes["2025-01"],
        "jan_cohort_month0_revenue": cohorts["2025-01"][0],
        "jan_cohort_m3_retention_pct": ret("2025-01", 3),
        "jan_cohort_m6_retention_pct": ret("2025-01", 6),
        "apr_cohort_m3_retention_pct": ret("2025-04", 3),
        "best_m3_retention_cohort": best,
    })


# ---------------------------------------------------------------------------
@generator("budget-variance-fx-001")
def gen_budget_fx(seed: int):
    rng = random.Random(seed)
    depts = [
        ("Engineering", "USD"), ("Sales", "USD"), ("Marketing", "GBP"),
        ("Customer Success", "EUR"), ("G&A", "USD"), ("EMEA Ops", "EUR"),
        ("APAC Ops", "JPY"), ("Data & Analytics", "GBP"),
    ]
    base_rates = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "JPY": 0.0068}
    rows = []
    for name, cur in depts:
        scale = 1000 if cur != "JPY" else 150_000
        budget_local = rng.randrange(400, 2_400, 25) * scale
        actual_local = int(budget_local * rng.uniform(0.85, 1.20))
        b_rate = base_rates[cur]
        a_rate = round(b_rate * (rng.uniform(0.94, 1.06) if cur != "USD" else 1.0), 4)
        rows.append([name, cur, budget_local, actual_local, b_rate, a_rate])
    _write_csv("budget-variance-fx-001", "opex_by_department.csv",
               ["department", "currency", "budget_local", "actual_local",
                "budget_fx_rate_to_usd", "actual_fx_rate_to_usd"], rows)

    tot_b = sum(r[2] * r[4] for r in rows)
    tot_a = sum(r[3] * r[5] for r in rows)
    fx_var = sum(r[3] * (r[5] - r[4]) for r in rows)
    org_var = sum((r[3] - r[2]) * r[4] for r in rows)
    worst = max(rows, key=lambda r: (r[3] - r[2]) * r[4])
    _write_key("budget-variance-fx-001", {
        "total_budget_usd": tot_b,
        "total_actual_usd": tot_a,
        "total_variance_usd": tot_a - tot_b,
        "fx_variance_usd": fx_var,
        "organic_variance_usd": org_var,
        "largest_organic_overspend_dept": worst[0],
    })


# ---------------------------------------------------------------------------
def _irr(cfs: list[float]) -> float:
    lo, hi = -0.99, 10.0
    def npv(r):
        return sum(cf / (1 + r) ** t for t, cf in enumerate(cfs))
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@generator("capital-allocation-001")
def gen_capital(seed: int):
    rng = random.Random(seed)
    debt = rng.randrange(20_000, 60_000, 1_000)
    equity = rng.randrange(60_000, 140_000, 1_000)
    kd = round(rng.uniform(5.5, 8.5), 2)
    tax = 25.0
    rf = round(rng.uniform(3.5, 4.6), 2)
    beta = round(rng.uniform(0.9, 1.6), 2)
    erp = round(rng.uniform(4.5, 6.0), 2)
    _write_csv("capital-allocation-001", "capital_structure.csv", ["parameter", "value"], [
        ["market_value_of_debt", debt], ["market_value_of_equity", equity],
        ["pretax_cost_of_debt_pct", kd], ["tax_rate_pct", tax],
        ["risk_free_rate_pct", rf], ["equity_beta", beta],
        ["equity_risk_premium_pct", erp],
    ])

    def project(front_loaded: bool):
        inv = rng.randrange(8_000, 18_000, 500)
        cfs = [-float(inv)]
        total = inv * rng.uniform(1.35, 1.9)
        weights = [0.30, 0.26, 0.20, 0.14, 0.10] if front_loaded else [0.08, 0.14, 0.20, 0.26, 0.32]
        for w in weights:
            cfs.append(m2(total * w))
        return cfs

    cfs_a, cfs_b = project(True), project(False)
    _write_csv("capital-allocation-001", "project_cash_flows.csv",
               ["year", "project_a", "project_b"],
               [[t, cfs_a[t], cfs_b[t]] for t in range(6)])

    ke = rf + beta * erp
    kd_at = kd * (1 - tax / 100)
    total_cap = debt + equity
    wacc = (equity / total_cap) * ke + (debt / total_cap) * kd_at
    r = wacc / 100

    def npv(cfs):
        return sum(cf / (1 + r) ** t for t, cf in enumerate(cfs))

    def payback(cfs):
        cum = cfs[0]
        for t in range(1, len(cfs)):
            if cum + cfs[t] >= 0:
                return (t - 1) + (-cum) / cfs[t]
            cum += cfs[t]
        return float("nan")

    npv_a, npv_b = npv(cfs_a), npv(cfs_b)
    _write_key("capital-allocation-001", {
        "wacc_pct": wacc,
        "npv_project_a": npv_a,
        "npv_project_b": npv_b,
        "irr_project_a_pct": _irr(cfs_a) * 100,
        "irr_project_b_pct": _irr(cfs_b) * 100,
        "payback_years_project_a": payback(cfs_a),
        "recommended_project": "A" if npv_a >= npv_b else "B",
    })


# ---------------------------------------------------------------------------
@generator("unit-economics-001")
def gen_unit_econ(seed: int):
    rng = random.Random(seed)
    budget = rng.randrange(300_000, 600_000, 25_000)
    channels = []
    for name in ["Paid Search", "Paid Social", "Affiliates", "Direct Mail"]:
        cac = m2(rng.uniform(25, 120))
        aov = m2(rng.uniform(60, 260))
        gm = round(rng.uniform(38, 62), 1)
        fulfill = m2(rng.uniform(4, 14))
        cap = rng.randrange(1_000, 6_000, 250)
        channels.append([name, cac, aov, gm, fulfill, cap])
    _write_csv("unit-economics-001", "channels.csv",
               ["channel", "cac", "avg_order_value", "gross_margin_pct",
                "fulfillment_cost_per_order", "max_monthly_orders"], channels)
    _write_csv("unit-economics-001", "parameters.csv", ["parameter", "value"],
               [["monthly_marketing_budget", budget]])

    # contribution per order (before CAC) and per CAC dollar
    enriched = []
    for name, cac, aov, gm, ful, cap in channels:
        contrib = aov * gm / 100 - ful - cac  # per-order contribution net of CAC
        roi = contrib / cac
        enriched.append((name, cac, cap, contrib, roi))
    # greedy: fill channels in descending contribution-per-CAC-dollar while contribution > 0
    remaining = float(budget)
    total_orders = 0
    total_contrib = 0.0
    for name, cac, cap, contrib, roi in sorted(enriched, key=lambda e: -e[4]):
        if contrib <= 0 or remaining <= 0:
            continue
        orders = min(cap, int(remaining // cac))
        remaining -= orders * cac
        total_orders += orders
        total_contrib += orders * contrib
    best = max(enriched, key=lambda e: e[4])
    _write_key("unit-economics-001", {
        "best_channel_by_contribution_per_cac_dollar": best[0],
        "best_channel_contribution_per_order": best[3],
        "optimal_total_orders": total_orders,
        "optimal_total_contribution": total_contrib,
        "unspent_budget": remaining,
    })


# ---------------------------------------------------------------------------
@generator("working-capital-001")
def gen_working_capital(seed: int):
    rng = random.Random(seed)
    rev = rng.randrange(60_000_000, 240_000_000, 1_000_000)
    cogs = int(rev * rng.uniform(0.45, 0.65))
    ar = int(rev * rng.uniform(0.10, 0.17))
    inv = int(cogs * rng.uniform(0.12, 0.22))
    ap = int(cogs * rng.uniform(0.08, 0.15))
    improve = rng.choice([5, 6, 7, 8, 10])
    _write_csv("working-capital-001", "financials.csv", ["line_item", "value"], [
        ["fy_revenue", rev], ["fy_cogs", cogs],
        ["avg_accounts_receivable", ar], ["avg_inventory", inv],
        ["avg_accounts_payable", ap], ["dso_improvement_days", improve],
    ])
    dso = ar / rev * 365
    dio = inv / cogs * 365
    dpo = ap / cogs * 365
    _write_key("working-capital-001", {
        "dso_days": dso, "dio_days": dio, "dpo_days": dpo,
        "cash_conversion_cycle_days": dso + dio - dpo,
        "cash_freed_by_dso_improvement": improve / 365 * rev,
    })


# ---------------------------------------------------------------------------
@generator("forecast-revrec-001")
def gen_revrec(seed: int):
    rng = random.Random(seed)
    quota = rng.randrange(200_000, 400_000, 25_000)  # per fully-ramped rep per quarter
    ramp = [0.25, 0.50, 0.75, 1.00]
    seasonality = [0.85, 0.95, 1.00, 1.20]
    # reps by hire quarter: hired before 2026 are fully ramped
    ramped_reps = rng.randint(6, 12)
    hires = [rng.randint(1, 4) for _ in range(4)]  # new reps hired at start of Q1..Q4 2026
    prior_bookings = [rng.randrange(1_200_000, 2_600_000, 50_000) for _ in range(3)]  # Q2-Q4 2025

    _write_csv("forecast-revrec-001", "sales_capacity.csv", ["parameter", "value"], [
        ["fully_ramped_reps_at_jan1_2026", ramped_reps],
        ["new_hires_q1_2026", hires[0]], ["new_hires_q2_2026", hires[1]],
        ["new_hires_q3_2026", hires[2]], ["new_hires_q4_2026", hires[3]],
        ["quarterly_quota_fully_ramped", quota],
    ])
    _write_csv("forecast-revrec-001", "ramp_and_seasonality.csv",
               ["quarter_of_tenure_or_fiscal_quarter", "ramp_productivity_pct", "seasonality_multiplier"],
               [[i + 1, int(ramp[i] * 100), seasonality[i]] for i in range(4)])
    _write_csv("forecast-revrec-001", "prior_bookings.csv", ["quarter", "bookings"], [
        ["2025-Q2", prior_bookings[0]], ["2025-Q3", prior_bookings[1]], ["2025-Q4", prior_bookings[2]],
    ])

    bookings = []
    for q in range(4):  # 2026 Q1..Q4
        capacity = ramped_reps * 1.0
        for hq in range(q + 1):
            tenure_q = q - hq  # 0-indexed quarter of tenure
            capacity += hires[hq] * ramp[tenure_q]
        bookings.append(m2(capacity * quota * seasonality[q]))

    # revenue: bookings are 12-month contracts recognized ratably over 4 quarters
    # starting in the quarter of booking. Prior-year bookings feed the tail.
    all_b = prior_bookings + bookings  # index 0..2 = 2025 Q2..Q4, 3..6 = 2026 Q1..Q4
    revenue = []
    for q in range(3, 7):
        rev_q = sum(all_b[j] / 4 for j in range(max(0, q - 3), q + 1))
        revenue.append(rev_q)

    _write_key("forecast-revrec-001", {
        "bookings_2026_q1": bookings[0], "bookings_2026_q2": bookings[1],
        "bookings_2026_q3": bookings[2], "bookings_2026_q4": bookings[3],
        "total_bookings_2026": sum(bookings),
        "revenue_2026_q1": revenue[0], "revenue_2026_q2": revenue[1],
        "revenue_2026_q3": revenue[2], "revenue_2026_q4": revenue[3],
        "total_revenue_2026": sum(revenue),
    })


# ---------------------------------------------------------------------------
@generator("error-detection-001")
def gen_error_detection(seed: int):
    rng = random.Random(seed)
    rev = rng.randrange(30_000, 80_000, 500)
    cogs = int(rev * rng.uniform(0.38, 0.55))
    opex_lines = {
        "sales_and_marketing": int(rev * rng.uniform(0.12, 0.22)),
        "research_and_development": int(rev * rng.uniform(0.10, 0.18)),
        "general_and_administrative": int(rev * rng.uniform(0.06, 0.12)),
    }
    dep = int(rev * rng.uniform(0.02, 0.05))
    interest = int(rev * rng.uniform(0.005, 0.02))
    tax_rate = 0.25

    true_gross = rev - cogs
    true_opex = sum(opex_lines.values())
    true_op_inc = true_gross - true_opex - dep
    true_pretax = true_op_inc - interest
    true_tax = round(max(0, true_pretax) * tax_rate)
    true_ni = true_pretax - true_tax

    # inject errors into the *subtotals* (components are authoritative)
    err = lambda v: int(v * rng.choice([0.92, 0.95, 1.06, 1.1])) + rng.choice([113, -87, 250])
    reported = [
        ["revenue", rev], ["cogs", cogs],
        ["gross_profit", err(true_gross)],
        ["sales_and_marketing", opex_lines["sales_and_marketing"]],
        ["research_and_development", opex_lines["research_and_development"]],
        ["general_and_administrative", opex_lines["general_and_administrative"]],
        ["total_operating_expenses", err(true_opex)],
        ["depreciation", dep],
        ["operating_income", err(true_op_inc)],
        ["interest_expense", interest],
        ["pretax_income", err(true_pretax)],
        ["tax_rate_pct", 25],
        ["tax_expense", err(true_tax)],
        ["net_income", err(true_ni)],
    ]
    _write_csv("error-detection-001", "reported_pnl.csv", ["line_item", "value"], reported)
    _write_key("error-detection-001", {
        "correct_gross_profit": true_gross,
        "correct_total_operating_expenses": true_opex,
        "correct_operating_income": true_op_inc,
        "correct_pretax_income": true_pretax,
        "correct_tax_expense": true_tax,
        "correct_net_income": true_ni,
    })


# ---------------------------------------------------------------------------
@generator("board-memo-001")
def gen_board_memo(seed: int):
    rng = random.Random(seed)
    # Construct a quarter with two dominant, discoverable drivers:
    # 1) revenue miss concentrated in EMEA (churned enterprise logos)
    # 2) favorable opex from delayed hiring
    regions = ["NA", "EMEA", "APAC"]
    rev_rows = []
    facts = {}
    for reg in regions:
        b = rng.randrange(4_000, 9_000, 100)
        miss = 0.82 if reg == "EMEA" else rng.uniform(0.98, 1.04)
        a = int(b * miss)
        rev_rows.append([reg, b, a])
    _write_csv("board-memo-001", "revenue_by_region.csv",
               ["region", "budget_q3", "actual_q3"], rev_rows)

    opex_rows = []
    for dept, favorable in [("R&D", True), ("S&M", False), ("G&A", False)]:
        b = rng.randrange(1_500, 4_000, 50)
        a = int(b * (0.87 if favorable else rng.uniform(0.98, 1.03)))
        opex_rows.append([dept, b, a])
    _write_csv("board-memo-001", "opex_by_department.csv",
               ["department", "budget_q3", "actual_q3"], opex_rows)

    kpi_rows = [
        ["enterprise_logos_churned_emea", rng.randint(3, 6)],
        ["enterprise_logos_churned_other", rng.randint(0, 1)],
        ["open_headcount_rd_unfilled", rng.randint(8, 15)],
        ["ndr_pct", round(rng.uniform(96, 102), 1)],
        ["cash_balance_eoq", rng.randrange(18_000, 40_000, 500)],
    ]
    _write_csv("board-memo-001", "kpis.csv", ["kpi", "value"], kpi_rows)

    tot_rev_b = sum(r[1] for r in rev_rows)
    tot_rev_a = sum(r[2] for r in rev_rows)
    tot_opex_b = sum(r[1] for r in opex_rows)
    tot_opex_a = sum(r[2] for r in opex_rows)
    facts = {
        "total_revenue_budget": tot_rev_b,
        "total_revenue_actual": tot_rev_a,
        "revenue_variance": tot_rev_a - tot_rev_b,
        "primary_revenue_driver": "EMEA enterprise churn",
        "emea_revenue_variance": rev_rows[1][2] - rev_rows[1][1],
        "total_opex_budget": tot_opex_b,
        "total_opex_actual": tot_opex_a,
        "opex_variance_favorable": tot_opex_b - tot_opex_a,
        "primary_opex_driver": "R&D underspend from unfilled headcount",
        "kpis": dict(kpi_rows),
    }
    _write_key("board-memo-001", facts)


def generate_all(seed: int = 42, only: str | None = None):
    for task_id, fn in GENERATORS.items():
        if only and task_id != only:
            continue
        # derive a distinct, deterministic per-task seed so tasks are independent
        task_seed = seed * 1_000_003 + zlib.crc32(task_id.encode())
        fn(task_seed)
        print(f"generated {task_id} (seed {seed})")
