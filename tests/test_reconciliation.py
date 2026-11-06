import pandas as pd

from src.reconciliation import run_reconciliation_checks
from src.risk_analytics import calculate_risk_metrics


def test_reconciliation_pass_and_review():
    df = pd.DataFrame(
        [
            {
                "company_id": "CMP0001",
                "ticker": "C001",
                "sector": "Banking",
                "fiscal_period": "2025Q1",
                "total_assets": 1000.0,
                "total_liabilities": 600.0,
                "shareholder_equity": 400.0,
                "source_system": "ERP_A",
            },
            {
                "company_id": "CMP0002",
                "ticker": "C002",
                "sector": "NBFC",
                "fiscal_period": "2025Q1",
                "total_assets": 1000.0,
                "total_liabilities": 600.0,
                "shareholder_equity": 250.0,
                "source_system": "ERP_B",
            },
        ]
    )
    audit = run_reconciliation_checks(df, tolerance_ratio=0.02)
    statuses = dict(zip(audit["company_id"], audit["reconciliation_status"]))
    assert statuses["CMP0001"] == "Pass"
    assert statuses["CMP0002"] == "Review"


def test_risk_metric_calculation():
    exposures = pd.DataFrame(
        [
            {
                "company_id": "CMP0001",
                "ticker": "C001",
                "sector": "Banking",
                "market_value": 1000000.0,
                "duration_years": 4.0,
                "pv01": 400.0,
                "cs01": 80.0,
                "hedge_notional": 900000.0,
                "hedge_pv01": -380.0,
                "exposure_value": 500000.0,
                "collateral_value": 600000.0,
                "hql_assets": 120000.0,
                "net_cash_outflows_30d": 100000.0,
            }
        ]
    )
    metrics = calculate_risk_metrics(exposures)
    assert round(metrics.loc[0, "hedge_ratio"], 2) == 0.95
    assert round(metrics.loc[0, "lcr_percent"], 2) == 120.00
    assert round(metrics.loc[0, "collateral_coverage_ratio"], 2) == 1.20
