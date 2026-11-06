"""ETL routines for cleaning and standardizing financial statement data."""

from __future__ import annotations

import pandas as pd

from src.config import CLEAN_FINANCIALS_PATH, RAW_FINANCIALS_PATH, TICKER_MASTER_PATH, ensure_directories

NUMERIC_COLUMNS = [
    "revenue",
    "cogs",
    "operating_expense",
    "net_income",
    "operating_cash_flow",
    "total_assets",
    "total_liabilities",
    "shareholder_equity",
]

REQUIRED_COLUMNS = [
    "company_id",
    "company_name",
    "ticker",
    "sector",
    "fiscal_period",
    "reporting_currency",
    *NUMERIC_COLUMNS,
    "source_system",
]


def load_raw_financials(path=RAW_FINANCIALS_PATH) -> pd.DataFrame:
    """Load raw financial statement records from CSV."""
    return pd.read_csv(path)


def clean_financials(raw_df: pd.DataFrame, ticker_master_path=TICKER_MASTER_PATH) -> pd.DataFrame:
    """Clean, normalize, map tickers, and derive period fields."""
    df = raw_df.copy()
    df.columns = [col.strip().lower() for col in df.columns]

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    # Normalize text fields.
    for col in ["company_id", "company_name", "ticker", "sector", "fiscal_period", "reporting_currency", "source_system"]:
        df[col] = df[col].astype("string").str.strip()

    df["company_id"] = df["company_id"].str.upper()
    df["ticker"] = df["ticker"].str.upper()
    df["reporting_currency"] = df["reporting_currency"].str.upper()

    # Map missing tickers/sectors using a master reference table.
    ticker_master = pd.read_csv(ticker_master_path)
    ticker_master.columns = [col.strip().lower() for col in ticker_master.columns]
    ticker_master["company_id"] = ticker_master["company_id"].astype("string").str.upper().str.strip()
    ticker_master["ticker"] = ticker_master["ticker"].astype("string").str.upper().str.strip()

    df = df.merge(
        ticker_master[["company_id", "ticker", "sector"]].rename(
            columns={"ticker": "master_ticker", "sector": "master_sector"}
        ),
        on="company_id",
        how="left",
    )
    df["ticker"] = df["ticker"].fillna(df["master_ticker"])
    df["sector"] = df["sector"].fillna(df["master_sector"])
    df.drop(columns=["master_ticker", "master_sector"], inplace=True)

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derive year and quarter for cross-period checks.
    period_parts = df["fiscal_period"].str.extract(r"(?P<fiscal_year>\d{4})Q(?P<fiscal_quarter>[1-4])")
    df["fiscal_year"] = pd.to_numeric(period_parts["fiscal_year"], errors="coerce").astype("Int64")
    df["fiscal_quarter"] = pd.to_numeric(period_parts["fiscal_quarter"], errors="coerce").astype("Int64")

    # Keep a consistent sort order for downstream reporting.
    df.sort_values(["company_id", "fiscal_year", "fiscal_quarter"], inplace=True, ignore_index=True)
    return df


def save_clean_financials(clean_df: pd.DataFrame, path=CLEAN_FINANCIALS_PATH) -> None:
    ensure_directories()
    clean_df.to_csv(path, index=False)


def run_etl() -> pd.DataFrame:
    """Execute the ETL step and save the cleaned dataset."""
    raw_df = load_raw_financials()
    clean_df = clean_financials(raw_df)
    save_clean_financials(clean_df)
    return clean_df
