"""Portfolio risk, stress scenario, collateral, LCR, and hedge effectiveness analytics."""

from __future__ import annotations

import pandas as pd

from src.config import PORTFOLIO_EXPOSURE_PATH

SCENARIOS = {
    "base_case": {"rate_shock_bps": 0, "spread_shock_bps": 0, "collateral_erosion_pct": 0.00},
    "rate_up_100bps": {"rate_shock_bps": 100, "spread_shock_bps": 0, "collateral_erosion_pct": 0.00},
    "rate_down_50bps": {"rate_shock_bps": -50, "spread_shock_bps": 0, "collateral_erosion_pct": 0.00},
    "credit_spread_plus_75bps": {"rate_shock_bps": 0, "spread_shock_bps": 75, "collateral_erosion_pct": 0.00},
    "collateral_erosion_15pct": {"rate_shock_bps": 0, "spread_shock_bps": 0, "collateral_erosion_pct": 0.15},
    "combined_stress": {"rate_shock_bps": 100, "spread_shock_bps": 75, "collateral_erosion_pct": 0.15},
}


def load_exposures(path=PORTFOLIO_EXPOSURE_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def calculate_risk_metrics(exposures: pd.DataFrame) -> pd.DataFrame:
    """Calculate base risk ratios used across stress reports."""
    df = exposures.copy()
    df["hedge_ratio"] = (-df["hedge_pv01"] / df["pv01"].replace(0, pd.NA)).astype(float)
    df["pv01_gap"] = df["pv01"] + df["hedge_pv01"]
    df["lcr_percent"] = (df["hql_assets"] / df["net_cash_outflows_30d"].replace(0, pd.NA) * 100).astype(float)
    df["collateral_coverage_ratio"] = (df["collateral_value"] / df["exposure_value"].replace(0, pd.NA)).astype(float)
    df["hedge_status"] = df["hedge_ratio"].apply(lambda x: "Aligned" if 0.80 <= x <= 1.25 else "Review")
    df["lcr_status"] = df["lcr_percent"].apply(lambda x: "Pass" if x >= 100 else "Breach")
    df["collateral_status"] = df["collateral_coverage_ratio"].apply(lambda x: "Pass" if x >= 1.05 else "Breach")
    return df


def run_stress_scenarios(exposures: pd.DataFrame) -> pd.DataFrame:
    """Create scenario-level P&L and adequacy metrics."""
    base = calculate_risk_metrics(exposures)
    records: list[dict[str, object]] = []

    for scenario_name, params in SCENARIOS.items():
        scenario = base.copy()
        rate_shock = params["rate_shock_bps"]
        spread_shock = params["spread_shock_bps"]
        erosion = params["collateral_erosion_pct"]

        scenario["scenario"] = scenario_name
        scenario["rate_shock_bps"] = rate_shock
        scenario["spread_shock_bps"] = spread_shock
        scenario["collateral_erosion_pct"] = erosion
        scenario["rate_shock_pnl"] = -scenario["pv01_gap"] * rate_shock
        scenario["spread_shock_pnl"] = -scenario["cs01"] * spread_shock
        scenario["total_stress_pnl"] = scenario["rate_shock_pnl"] + scenario["spread_shock_pnl"]
        scenario["stressed_collateral_value"] = scenario["collateral_value"] * (1 - erosion)
        scenario["stressed_collateral_coverage_ratio"] = scenario["stressed_collateral_value"] / scenario["exposure_value"].replace(0, pd.NA)
        scenario["stress_pnl_to_market_value_pct"] = scenario["total_stress_pnl"] / scenario["market_value"].replace(0, pd.NA) * 100
        records.append(scenario)

    report = pd.concat(records, ignore_index=True)
    selected_cols = [
        "scenario",
        "company_id",
        "ticker",
        "sector",
        "market_value",
        "duration_years",
        "pv01",
        "hedge_pv01",
        "hedge_ratio",
        "pv01_gap",
        "cs01",
        "rate_shock_bps",
        "spread_shock_bps",
        "rate_shock_pnl",
        "spread_shock_pnl",
        "total_stress_pnl",
        "stress_pnl_to_market_value_pct",
        "lcr_percent",
        "collateral_coverage_ratio",
        "stressed_collateral_coverage_ratio",
        "hedge_status",
        "lcr_status",
        "collateral_status",
    ]
    return report[selected_cols]


def build_risk_breach_log(scenario_report: pd.DataFrame) -> pd.DataFrame:
    """Create a compliance-style breach log from risk scenario outputs."""
    breaches: list[dict[str, object]] = []

    for _, row in scenario_report.iterrows():
        if row["hedge_status"] == "Review":
            breaches.append(_breach(row, "HEDGE001", "Medium", "Hedge ratio outside 80%-125% control band", row["hedge_ratio"], "0.80 to 1.25"))
        if row["lcr_status"] == "Breach":
            breaches.append(_breach(row, "LIQ001", "High", "LCR below 100% minimum threshold", row["lcr_percent"], ">= 100%"))
        if row["collateral_status"] == "Breach":
            breaches.append(_breach(row, "COLL001", "High", "Base collateral coverage below threshold", row["collateral_coverage_ratio"], ">= 1.05x"))
        if row["stressed_collateral_coverage_ratio"] < 1.0:
            breaches.append(_breach(row, "COLL002", "High", "Stressed collateral coverage below 1.0x", row["stressed_collateral_coverage_ratio"], ">= 1.00x"))
        if abs(row["stress_pnl_to_market_value_pct"]) > 2.5:
            breaches.append(_breach(row, "STRESS001", "Medium", "Stress P&L exceeds 2.5% of market value", row["stress_pnl_to_market_value_pct"], "Within +/-2.5%"))

    return pd.DataFrame(breaches).drop_duplicates()


def _breach(row: pd.Series, rule_id: str, severity: str, issue: str, current_value, expected_value) -> dict[str, object]:
    return {
        "scenario": row["scenario"],
        "rule_id": rule_id,
        "severity": severity,
        "company_id": row["company_id"],
        "ticker": row["ticker"],
        "sector": row["sector"],
        "issue": issue,
        "current_value": round(float(current_value), 4),
        "expected_value": expected_value,
    }
