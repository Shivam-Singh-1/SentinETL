"""Generate sample data for the reconciliation and risk monitoring project.

The generated data is intentionally realistic enough for a resume/GitHub project,
but small enough to understand during interviews.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import PORTFOLIO_EXPOSURE_PATH, RAW_FINANCIALS_PATH, TICKER_MASTER_PATH, ensure_directories

SECTORS = [
    "Banking",
    "NBFC",
    "Insurance",
    "Manufacturing",
    "Technology",
    "Consumer",
    "Energy",
    "Healthcare",
]

CURRENCIES = ["INR", "USD"]


def _make_periods() -> list[str]:
    return [f"{year}Q{quarter}" for year in range(2023, 2026) for quarter in range(1, 5)]


def generate_sample_data(num_companies: int = 120, seed: int = 42) -> None:
    """Generate raw financials, ticker master, and portfolio exposure data."""
    ensure_directories()
    rng = np.random.default_rng(seed)

    company_ids = [f"CMP{i:04d}" for i in range(1, num_companies + 1)]
    company_names = [f"Company {i:04d} Ltd" for i in range(1, num_companies + 1)]
    tickers = [f"C{i:03d}" for i in range(1, num_companies + 1)]
    sectors = rng.choice(SECTORS, size=num_companies)

    ticker_master = pd.DataFrame(
        {
            "company_id": company_ids,
            "company_name": company_names,
            "ticker": tickers,
            "sector": sectors,
            "is_active": True,
        }
    )
    ticker_master.to_csv(TICKER_MASTER_PATH, index=False)

    periods = _make_periods()
    rows: list[dict[str, object]] = []

    for idx, company_id in enumerate(company_ids):
        base_revenue = rng.uniform(500, 9000)
        base_assets = rng.uniform(2000, 25000)
        company_growth = rng.normal(0.035, 0.025)
        currency = rng.choice(CURRENCIES, p=[0.78, 0.22])

        for period_index, period in enumerate(periods):
            seasonal_factor = 1 + 0.04 * np.sin(period_index / 2)
            revenue = base_revenue * ((1 + company_growth) ** period_index) * seasonal_factor
            revenue *= rng.normal(1.0, 0.05)

            cogs = revenue * rng.uniform(0.42, 0.68)
            opex = revenue * rng.uniform(0.12, 0.28)
            net_income = revenue - cogs - opex - rng.uniform(5, 80)
            operating_cash_flow = net_income * rng.uniform(0.75, 1.25)

            assets = base_assets * ((1 + company_growth / 2) ** period_index) * rng.normal(1.0, 0.03)
            liabilities = assets * rng.uniform(0.35, 0.72)
            equity = assets - liabilities

            rows.append(
                {
                    "company_id": company_id,
                    "company_name": company_names[idx],
                    "ticker": tickers[idx],
                    "sector": sectors[idx],
                    "fiscal_period": period,
                    "reporting_currency": currency,
                    "revenue": round(revenue, 2),
                    "cogs": round(cogs, 2),
                    "operating_expense": round(opex, 2),
                    "net_income": round(net_income, 2),
                    "operating_cash_flow": round(operating_cash_flow, 2),
                    "total_assets": round(assets, 2),
                    "total_liabilities": round(liabilities, 2),
                    "shareholder_equity": round(equity, 2),
                    "source_system": rng.choice(["ERP_A", "ERP_B", "Manual_Upload"], p=[0.48, 0.42, 0.10]),
                }
            )

    financials = pd.DataFrame(rows)

    # Inject issues deliberately so that validation and audit tables have useful examples.
    financials = _inject_data_quality_issues(financials, rng)
    financials.to_csv(RAW_FINANCIALS_PATH, index=False)

    exposures = _generate_portfolio_exposures(ticker_master, rng)
    exposures.to_csv(PORTFOLIO_EXPOSURE_PATH, index=False)


def _inject_data_quality_issues(financials: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    output = financials.copy()

    # Missing tickers for mapping test.
    missing_ticker_idx = rng.choice(output.index, size=max(8, len(output) // 120), replace=False)
    output.loc[missing_ticker_idx, "ticker"] = np.nan

    # Missing numeric values for null profiling.
    missing_revenue_idx = rng.choice(output.index, size=max(8, len(output) // 150), replace=False)
    output.loc[missing_revenue_idx, "revenue"] = np.nan

    # Outlier revenue for screening.
    outlier_idx = rng.choice(output.index, size=6, replace=False)
    output.loc[outlier_idx, "revenue"] = output.loc[outlier_idx, "revenue"] * rng.uniform(4.0, 8.0)

    # Accounting equation breaks.
    recon_break_idx = rng.choice(output.index, size=10, replace=False)
    output.loc[recon_break_idx, "shareholder_equity"] = output.loc[recon_break_idx, "shareholder_equity"] * rng.uniform(0.75, 0.92)

    # Add duplicate rows.
    duplicate_rows = output.sample(n=12, random_state=17)
    output = pd.concat([output, duplicate_rows], ignore_index=True)

    # One clear negative value case.
    negative_idx = rng.choice(output.index, size=3, replace=False)
    output.loc[negative_idx, "total_assets"] = -abs(output.loc[negative_idx, "total_assets"])

    return output


def _generate_portfolio_exposures(ticker_master: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for _, row in ticker_master.iterrows():
        market_value = rng.uniform(25_000_000, 350_000_000)
        duration_years = rng.uniform(0.5, 7.0)
        pv01 = market_value * duration_years * 0.0001
        cs01 = market_value * rng.uniform(0.00003, 0.00016)
        hedge_ratio = rng.normal(0.95, 0.18)
        hedge_pv01 = -pv01 * hedge_ratio
        exposure_value = market_value * rng.uniform(0.35, 0.95)
        collateral_value = exposure_value * rng.uniform(0.85, 1.35)
        hqla = rng.uniform(15_000_000, 250_000_000)
        net_cash_outflows = hqla / rng.uniform(0.75, 1.8)

        records.append(
            {
                "company_id": row["company_id"],
                "ticker": row["ticker"],
                "sector": row["sector"],
                "market_value": round(market_value, 2),
                "duration_years": round(duration_years, 2),
                "pv01": round(pv01, 2),
                "cs01": round(cs01, 2),
                "hedge_notional": round(market_value * rng.uniform(0.25, 0.95), 2),
                "hedge_pv01": round(hedge_pv01, 2),
                "exposure_value": round(exposure_value, 2),
                "collateral_value": round(collateral_value, 2),
                "hql_assets": round(hqla, 2),
                "net_cash_outflows_30d": round(net_cash_outflows, 2),
            }
        )
    return pd.DataFrame(records)
