"""Command-line entry point for the project.

Usage:
    python main.py --run-all
    python main.py --generate-sample-data
"""

from __future__ import annotations

import argparse

import pandas as pd

from src.config import (
    ANALYST_READY_PATH,
    CLEAN_FINANCIALS_PATH,
    DQ_ISSUE_LOG_PATH,
    DQ_SUMMARY_PATH,
    MANAGEMENT_EXCEL_PATH,
    MANAGEMENT_MD_PATH,
    RAW_FINANCIALS_PATH,
    RECON_AUDIT_PATH,
    RISK_BREACH_PATH,
    RISK_SCENARIO_PATH,
    ensure_directories,
)
from src.data_generator import generate_sample_data
from src.data_quality import build_quality_summary, estimate_completeness_improvement, validate_financials
from src.etl import load_raw_financials, run_etl
from src.reconciliation import create_analyst_ready_dataset, run_reconciliation_checks
from src.reporting import export_management_excel, write_management_summary
from src.risk_analytics import build_risk_breach_log, load_exposures, run_stress_scenarios


def run_full_pipeline() -> None:
    ensure_directories()

    if not RAW_FINANCIALS_PATH.exists():
        print("Sample data not found. Generating sample data...")
        generate_sample_data()

    print("Running ETL...")
    raw_df = load_raw_financials()
    clean_df = run_etl()
    clean_df.to_csv(CLEAN_FINANCIALS_PATH, index=False)

    print("Running data quality checks...")
    issue_log = validate_financials(clean_df)
    quality_summary = build_quality_summary(clean_df, issue_log)
    issue_log.to_csv(DQ_ISSUE_LOG_PATH, index=False)
    quality_summary.to_csv(DQ_SUMMARY_PATH, index=False)

    print("Running reconciliation checks...")
    reconciliation_audit = run_reconciliation_checks(clean_df)
    analyst_ready = create_analyst_ready_dataset(clean_df, reconciliation_audit)
    reconciliation_audit.to_csv(RECON_AUDIT_PATH, index=False)
    analyst_ready.to_csv(ANALYST_READY_PATH, index=False)

    print("Running risk analytics and stress scenarios...")
    exposures = load_exposures()
    risk_scenario_report = run_stress_scenarios(exposures)
    risk_breach_log = build_risk_breach_log(risk_scenario_report)
    risk_scenario_report.to_csv(RISK_SCENARIO_PATH, index=False)
    risk_breach_log.to_csv(RISK_BREACH_PATH, index=False)

    print("Exporting management reports...")
    completeness_improvement = estimate_completeness_improvement(raw_df, clean_df)
    export_management_excel(quality_summary, issue_log, reconciliation_audit, risk_scenario_report, risk_breach_log)
    write_management_summary(
        quality_summary,
        issue_log,
        reconciliation_audit,
        risk_scenario_report,
        risk_breach_log,
        completeness_improvement,
    )

    print("\nPipeline completed successfully.")
    print(f"Clean financials: {CLEAN_FINANCIALS_PATH}")
    print(f"Analyst-ready dataset: {ANALYST_READY_PATH}")
    print(f"Data quality log: {DQ_ISSUE_LOG_PATH}")
    print(f"Risk breach log: {RISK_BREACH_PATH}")
    print(f"Excel report: {MANAGEMENT_EXCEL_PATH}")
    print(f"Markdown summary: {MANAGEMENT_MD_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Financial reconciliation and data quality monitor")
    parser.add_argument("--generate-sample-data", action="store_true", help="Generate raw sample data only")
    parser.add_argument("--run-all", action="store_true", help="Run complete ETL, validation, reconciliation, risk, and reporting pipeline")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.generate_sample_data:
        generate_sample_data()
        print("Sample data generated.")
        return
    if args.run_all:
        run_full_pipeline()
        return

    print("No command selected. Running full pipeline by default.")
    run_full_pipeline()


if __name__ == "__main__":
    main()
