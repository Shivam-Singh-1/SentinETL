"""Data quality checks for financial fundamentals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.etl import NUMERIC_COLUMNS

KEY_COLUMNS = ["company_id", "ticker", "fiscal_period"]


def build_null_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Return column-level null counts and null percentages."""
    total_rows = len(df)
    profile = pd.DataFrame(
        {
            "column_name": df.columns,
            "null_count": [int(df[col].isna().sum()) for col in df.columns],
            "null_percent": [round(float(df[col].isna().mean() * 100), 2) for col in df.columns],
            "total_rows": total_rows,
        }
    )
    return profile.sort_values("null_percent", ascending=False)


def _append_issue(issues: list[dict[str, object]], row: pd.Series | None, rule_id: str, severity: str, field: str, issue: str, current_value=None, expected_value=None) -> None:
    issues.append(
        {
            "rule_id": rule_id,
            "severity": severity,
            "company_id": None if row is None else row.get("company_id"),
            "ticker": None if row is None else row.get("ticker"),
            "fiscal_period": None if row is None else row.get("fiscal_period"),
            "field": field,
            "issue": issue,
            "current_value": current_value,
            "expected_value": expected_value,
        }
    )


def detect_duplicate_records(df: pd.DataFrame) -> pd.DataFrame:
    """Find duplicated company-period rows after cleaning."""
    duplicate_mask = df.duplicated(subset=KEY_COLUMNS, keep=False)
    return df.loc[duplicate_mask, KEY_COLUMNS + ["source_system"]].copy()


def detect_outliers_iqr(df: pd.DataFrame, columns: list[str] | None = None, iqr_multiplier: float = 3.0) -> pd.DataFrame:
    """Flag outliers using a simple IQR screen for explainability."""
    columns = columns or NUMERIC_COLUMNS
    records: list[dict[str, object]] = []

    for col in columns:
        series = df[col].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        flagged = df[(df[col] < lower) | (df[col] > upper)]
        for _, row in flagged.iterrows():
            records.append(
                {
                    "company_id": row["company_id"],
                    "ticker": row["ticker"],
                    "fiscal_period": row["fiscal_period"],
                    "field": col,
                    "current_value": row[col],
                    "expected_range": f"{round(lower, 2)} to {round(upper, 2)}",
                }
            )
    return pd.DataFrame(records)


def validate_financials(df: pd.DataFrame) -> pd.DataFrame:
    """Run row-level validation checks and return an issue log."""
    issues: list[dict[str, object]] = []

    required_not_null = ["company_id", "ticker", "fiscal_period", "revenue", "total_assets", "total_liabilities", "shareholder_equity"]
    for idx, row in df.iterrows():
        for col in required_not_null:
            if pd.isna(row[col]) or row[col] == "":
                _append_issue(issues, row, "DQ001", "High", col, "Required field is missing", row[col], "Non-null value")

        for col in ["revenue", "total_assets", "total_liabilities"]:
            if pd.notna(row[col]) and row[col] < 0:
                _append_issue(issues, row, "DQ002", "High", col, "Unexpected negative value", row[col], ">= 0")

        if pd.notna(row["cogs"]) and pd.notna(row["revenue"]) and row["revenue"] > 0:
            gross_margin = (row["revenue"] - row["cogs"]) / row["revenue"]
            if gross_margin < -0.2 or gross_margin > 0.9:
                _append_issue(issues, row, "DQ003", "Medium", "cogs", "Gross margin outside normal review range", round(gross_margin, 4), "-20% to 90%")

    duplicate_rows = detect_duplicate_records(df)
    for _, row in duplicate_rows.iterrows():
        _append_issue(issues, row, "DQ004", "High", "company_id,ticker,fiscal_period", "Duplicate company-period record", "Duplicate", "Unique company-period")

    outliers = detect_outliers_iqr(df, columns=["revenue", "net_income", "total_assets"])
    for _, row in outliers.iterrows():
        _append_issue(
            issues,
            row,
            "DQ005",
            "Medium",
            row["field"],
            "Outlier detected using IQR screening",
            row["current_value"],
            row["expected_range"],
        )

    issues.extend(_cross_period_consistency_issues(df))

    return pd.DataFrame(issues)


def _cross_period_consistency_issues(df: pd.DataFrame) -> list[dict[str, object]]:
    """Flag missing periods and unusual quarter-on-quarter movements."""
    issues: list[dict[str, object]] = []
    sorted_df = df.sort_values(["company_id", "fiscal_year", "fiscal_quarter"])

    for company_id, group in sorted_df.groupby("company_id"):
        unique_periods = group["fiscal_period"].dropna().unique()
        if len(unique_periods) < 10:
            sample = group.iloc[0]
            _append_issue(issues, sample, "DQ006", "Medium", "fiscal_period", "Company has fewer periods than expected", len(unique_periods), ">= 10 periods")

        clean_group = group.drop_duplicates(subset=["fiscal_period"]).copy()
        clean_group["revenue_qoq_change"] = clean_group["revenue"].pct_change(fill_method=None)
        abnormal = clean_group[clean_group["revenue_qoq_change"].abs() > 2.5]
        for _, row in abnormal.iterrows():
            _append_issue(
                issues,
                row,
                "DQ007",
                "Medium",
                "revenue",
                "Quarter-on-quarter revenue movement requires review",
                round(row["revenue_qoq_change"], 4),
                "Change within +/-250%",
            )

    return issues


def build_quality_summary(df: pd.DataFrame, issue_log: pd.DataFrame) -> pd.DataFrame:
    """Create a company-level data quality score."""
    base = df[["company_id", "ticker", "sector"]].drop_duplicates(subset=["company_id"])
    if issue_log.empty:
        base["issue_count"] = 0
        base["high_severity_count"] = 0
        base["data_quality_score"] = 100
        return base

    counts = issue_log.groupby("company_id").agg(
        issue_count=("rule_id", "count"),
        high_severity_count=("severity", lambda x: int((x == "High").sum())),
        medium_severity_count=("severity", lambda x: int((x == "Medium").sum())),
    ).reset_index()

    summary = base.merge(counts, on="company_id", how="left").fillna(
        {"issue_count": 0, "high_severity_count": 0, "medium_severity_count": 0}
    )
    summary["data_quality_score"] = 100 - (summary["high_severity_count"] * 8) - (summary["medium_severity_count"] * 3)
    summary["data_quality_score"] = summary["data_quality_score"].clip(lower=0).round(0).astype(int)
    return summary.sort_values(["data_quality_score", "issue_count"])


def estimate_completeness_improvement(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> float:
    """Compare key-field completeness before and after ticker mapping and cleaning."""
    key_cols = ["company_id", "ticker", "fiscal_period", "revenue", "total_assets", "total_liabilities", "shareholder_equity"]
    raw_complete = raw_df[key_cols].notna().mean().mean()
    clean_complete = clean_df[key_cols].notna().mean().mean()
    if raw_complete == 0:
        return 0.0
    return round(float((clean_complete - raw_complete) / raw_complete * 100), 2)
