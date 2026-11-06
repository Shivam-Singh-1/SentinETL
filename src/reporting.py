"""Reporting helpers for CSV, Excel, and Markdown management summaries."""

from __future__ import annotations

import pandas as pd

from src.config import MANAGEMENT_EXCEL_PATH, MANAGEMENT_MD_PATH, ensure_directories


def export_management_excel(
    quality_summary: pd.DataFrame,
    issue_log: pd.DataFrame,
    reconciliation_audit: pd.DataFrame,
    risk_scenario_report: pd.DataFrame,
    risk_breach_log: pd.DataFrame,
    path=MANAGEMENT_EXCEL_PATH,
) -> None:
    """Create a multi-sheet Excel report similar to an ERM/management pack."""
    ensure_directories()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        quality_summary.to_excel(writer, index=False, sheet_name="Data Quality Summary")
        issue_log.to_excel(writer, index=False, sheet_name="DQ Issue Log")
        reconciliation_audit.to_excel(writer, index=False, sheet_name="Reconciliation Audit")
        risk_scenario_report.to_excel(writer, index=False, sheet_name="Risk Scenarios")
        risk_breach_log.to_excel(writer, index=False, sheet_name="Risk Breach Log")


def write_management_summary(
    quality_summary: pd.DataFrame,
    issue_log: pd.DataFrame,
    reconciliation_audit: pd.DataFrame,
    risk_scenario_report: pd.DataFrame,
    risk_breach_log: pd.DataFrame,
    completeness_improvement: float,
    path=MANAGEMENT_MD_PATH,
) -> None:
    """Write a short management-style Markdown summary."""
    total_companies = int(quality_summary["company_id"].nunique()) if not quality_summary.empty else 0
    total_issues = int(len(issue_log))
    high_issues = int((issue_log["severity"] == "High").sum()) if not issue_log.empty else 0
    recon_review = int((reconciliation_audit["reconciliation_status"] == "Review").sum()) if not reconciliation_audit.empty else 0
    risk_breaches = int(len(risk_breach_log))

    worst_quality = quality_summary.head(10)[["company_id", "ticker", "sector", "issue_count", "data_quality_score"]]
    top_risk = risk_breach_log.head(15) if not risk_breach_log.empty else pd.DataFrame()

    text = f"""# Management Summary

## Executive snapshot

- Companies monitored: **{total_companies}**
- Data quality issues found: **{total_issues}**
- High-severity data issues: **{high_issues}**
- Reconciliation rows requiring review: **{recon_review}**
- Risk/compliance breach rows: **{risk_breaches}**
- Estimated key-field completeness improvement after cleaning and ticker mapping: **{completeness_improvement}%**

## What the pipeline does

The pipeline ingests multi-period financial statement data, cleans text and numeric fields, maps missing tickers using a reference table, screens nulls and duplicates, flags outliers, validates cross-period consistency, and reconciles the accounting equation: total assets = total liabilities + shareholder equity.

The risk layer uses clean portfolio exposure inputs to calculate PV01 gaps, rate shock impact, credit spread stress, collateral coverage, LCR, and hedge effectiveness. Breach logs are written in a compliance-friendly format with rule id, severity, issue, current value, and expected threshold.

## Lowest data quality companies

{worst_quality.to_markdown(index=False)}

## Sample risk breaches

{top_risk.to_markdown(index=False) if not top_risk.empty else 'No risk breaches found.'}
"""
    ensure_directories()
    path.write_text(text, encoding="utf-8")
