"""Central paths used across the project."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
REFERENCE_DIR = DATA_DIR / "reference"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = ROOT_DIR / "outputs"

RAW_FINANCIALS_PATH = RAW_DIR / "sample_financial_statements.csv"
TICKER_MASTER_PATH = REFERENCE_DIR / "ticker_master.csv"
PORTFOLIO_EXPOSURE_PATH = RAW_DIR / "sample_portfolio_exposures.csv"

CLEAN_FINANCIALS_PATH = PROCESSED_DIR / "clean_financials.csv"
ANALYST_READY_PATH = OUTPUT_DIR / "analyst_ready_financials.csv"
DQ_ISSUE_LOG_PATH = OUTPUT_DIR / "data_quality_issue_log.csv"
DQ_SUMMARY_PATH = OUTPUT_DIR / "data_quality_summary.csv"
RECON_AUDIT_PATH = OUTPUT_DIR / "reconciliation_audit_table.csv"
RISK_SCENARIO_PATH = OUTPUT_DIR / "risk_scenario_report.csv"
RISK_BREACH_PATH = OUTPUT_DIR / "risk_breach_log.csv"
MANAGEMENT_EXCEL_PATH = OUTPUT_DIR / "management_report.xlsx"
MANAGEMENT_MD_PATH = OUTPUT_DIR / "management_summary.md"

REQUIRED_DIRS = [RAW_DIR, REFERENCE_DIR, PROCESSED_DIR, OUTPUT_DIR]


def ensure_directories() -> None:
    """Create required project folders if they do not already exist."""
    for folder in REQUIRED_DIRS:
        folder.mkdir(parents=True, exist_ok=True)
