"""Financial statement reconciliation checks."""

from __future__ import annotations

import pandas as pd


def run_reconciliation_checks(df: pd.DataFrame, tolerance_ratio: float = 0.02) -> pd.DataFrame:
    """Validate whether assets approximately equal liabilities plus equity.

    tolerance_ratio=0.02 means a 2% tolerance on total assets.
    """
    audit = df.copy()
    audit["liabilities_plus_equity"] = audit["total_liabilities"] + audit["shareholder_equity"]
    audit["reconciliation_difference"] = audit["total_assets"] - audit["liabilities_plus_equity"]
    audit["reconciliation_difference_abs"] = audit["reconciliation_difference"].abs()
    audit["reconciliation_difference_pct"] = (
        audit["reconciliation_difference_abs"] / audit["total_assets"].abs().replace(0, pd.NA)
    ).fillna(0)
    audit["reconciliation_status"] = audit["reconciliation_difference_pct"].apply(
        lambda value: "Pass" if value <= tolerance_ratio else "Review"
    )

    columns = [
        "company_id",
        "ticker",
        "sector",
        "fiscal_period",
        "total_assets",
        "total_liabilities",
        "shareholder_equity",
        "liabilities_plus_equity",
        "reconciliation_difference",
        "reconciliation_difference_pct",
        "reconciliation_status",
        "source_system",
    ]
    return audit[columns].sort_values(["reconciliation_status", "company_id", "fiscal_period"])


def create_analyst_ready_dataset(clean_df: pd.DataFrame, reconciliation_audit: pd.DataFrame) -> pd.DataFrame:
    """Join reconciliation status back to clean fundamentals."""
    status_cols = ["company_id", "ticker", "fiscal_period", "reconciliation_status", "reconciliation_difference_pct"]
    status_df = reconciliation_audit[status_cols].drop_duplicates(subset=["company_id", "ticker", "fiscal_period"], keep="first")
    output = clean_df.merge(status_df, on=["company_id", "ticker", "fiscal_period"], how="left")

    # Keep only one clean row per company-period for the analyst-ready layer.
    output = output.drop_duplicates(subset=["company_id", "ticker", "fiscal_period"], keep="first")

    output["gross_profit"] = output["revenue"] - output["cogs"]
    output["gross_margin_pct"] = (output["gross_profit"] / output["revenue"].replace(0, pd.NA) * 100).round(2)
    output["net_margin_pct"] = (output["net_income"] / output["revenue"].replace(0, pd.NA) * 100).round(2)
    output["debt_to_equity"] = (output["total_liabilities"] / output["shareholder_equity"].replace(0, pd.NA)).round(2)

    return output.sort_values(["company_id", "fiscal_year", "fiscal_quarter"])
