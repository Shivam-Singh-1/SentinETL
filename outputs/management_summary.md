# Management Summary

## Executive snapshot

- Companies monitored: **120**
- Data quality issues found: **41**
- High-severity data issues: **36**
- Reconciliation rows requiring review: **13**
- Risk/compliance breach rows: **1051**
- Estimated key-field completeness improvement after cleaning and ticker mapping: **0.12%**

## What the pipeline does

The pipeline ingests multi-period financial statement data, cleans text and numeric fields, maps missing tickers using a reference table, screens nulls and duplicates, flags outliers, validates cross-period consistency, and reconciles the accounting equation: total assets = total liabilities + shareholder equity.

The risk layer uses clean portfolio exposure inputs to calculate PV01 gaps, rate shock impact, credit spread stress, collateral coverage, LCR, and hedge effectiveness. Breach logs are written in a compliance-friendly format with rule id, severity, issue, current value, and expected threshold.

## Lowest data quality companies

| company_id   | ticker   | sector        |   issue_count |   data_quality_score |
|:-------------|:---------|:--------------|--------------:|---------------------:|
| CMP0007      | C007     | Banking       |             3 |                   76 |
| CMP0006      | C006     | Energy        |             2 |                   84 |
| CMP0010      | C010     | Banking       |             2 |                   84 |
| CMP0015      | C015     | Consumer      |             2 |                   84 |
| CMP0017      | C017     | Technology    |             2 |                   84 |
| CMP0053      | C053     | Insurance     |             2 |                   84 |
| CMP0057      | C057     | Technology    |             2 |                   84 |
| CMP0062      | C062     | Consumer      |             2 |                   84 |
| CMP0078      | C078     | NBFC          |             2 |                   84 |
| CMP0091      | C091     | Manufacturing |             2 |                   84 |

## Sample risk breaches

| scenario   | rule_id   | severity   | company_id   | ticker   | sector        | issue                                    |   current_value | expected_value   |
|:-----------|:----------|:-----------|:-------------|:---------|:--------------|:-----------------------------------------|----------------:|:-----------------|
| base_case  | COLL001   | High       | CMP0001      | C001     | Banking       | Base collateral coverage below threshold |          1.0403 | >= 1.05x         |
| base_case  | COLL001   | High       | CMP0002      | C002     | Energy        | Base collateral coverage below threshold |          0.9237 | >= 1.05x         |
| base_case  | COLL002   | High       | CMP0002      | C002     | Energy        | Stressed collateral coverage below 1.0x  |          0.9237 | >= 1.00x         |
| base_case  | COLL001   | High       | CMP0003      | C003     | Consumer      | Base collateral coverage below threshold |          0.9781 | >= 1.05x         |
| base_case  | COLL002   | High       | CMP0003      | C003     | Consumer      | Stressed collateral coverage below 1.0x  |          0.9781 | >= 1.00x         |
| base_case  | COLL001   | High       | CMP0005      | C005     | Manufacturing | Base collateral coverage below threshold |          0.8851 | >= 1.05x         |
| base_case  | COLL002   | High       | CMP0005      | C005     | Manufacturing | Stressed collateral coverage below 1.0x  |          0.8851 | >= 1.00x         |
| base_case  | LIQ001    | High       | CMP0006      | C006     | Energy        | LCR below 100% minimum threshold         |         76.3616 | >= 100%          |
| base_case  | COLL001   | High       | CMP0006      | C006     | Energy        | Base collateral coverage below threshold |          0.8832 | >= 1.05x         |
| base_case  | COLL002   | High       | CMP0006      | C006     | Energy        | Stressed collateral coverage below 1.0x  |          0.8832 | >= 1.00x         |
| base_case  | COLL001   | High       | CMP0007      | C007     | Banking       | Base collateral coverage below threshold |          0.8873 | >= 1.05x         |
| base_case  | COLL002   | High       | CMP0007      | C007     | Banking       | Stressed collateral coverage below 1.0x  |          0.8873 | >= 1.00x         |
| base_case  | LIQ001    | High       | CMP0009      | C009     | NBFC          | LCR below 100% minimum threshold         |         77.5897 | >= 100%          |
| base_case  | COLL001   | High       | CMP0009      | C009     | NBFC          | Base collateral coverage below threshold |          0.913  | >= 1.05x         |
| base_case  | COLL002   | High       | CMP0009      | C009     | NBFC          | Stressed collateral coverage below 1.0x  |          0.913  | >= 1.00x         |
