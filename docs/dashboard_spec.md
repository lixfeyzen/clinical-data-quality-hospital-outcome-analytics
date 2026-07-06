# Power BI Dashboard Specification

## Data Model

Recommended imported tables:

- `hospital_kpis.csv`
- `admission_outcomes_summary.csv`
- `diagnosis_profile.csv`
- `lab_summary.csv`
- `icu_utilization_summary.csv`
- `data_quality_checks.csv`

Main grain:

- `admission_outcomes_summary.csv`: aggregate by admission type
- `icu_utilization_summary.csv`: aggregate by admission type
- `diagnosis_profile.csv`: one row per ICD diagnosis code
- `lab_summary.csv`: one row per lab item

## Page 1: Overview

Purpose: give a recruiter or reviewer the project story in under one minute.

Visuals:

- KPI cards:
  - patients
  - admissions
  - ICU stays
  - diagnosis rows
  - lab events
  - mortality rate
  - median LOS
  - long LOS rate
- Bar chart: admissions by admission type
- Bar chart: admissions by race
- Bar chart: admissions by insurance
- Table: key data quality checks with status

## Page 2: Admission Outcomes

Purpose: summarize hospital admission outcomes and length-of-stay patterns.

Visuals:

- KPI cards:
  - hospital death admissions
  - mortality rate
  - median LOS
  - long LOS admissions
- Histogram or bin chart: LOS distribution
- Bar chart: long LOS rate by admission type
- Bar chart: mortality count by admission type
- Aggregate table:
  - `admission_type`
  - admissions
  - mortality rate
  - median LOS
  - long LOS rate
  - ICU admission rate

## Page 3: ICU Utilization

Purpose: show how admissions connect to ICU stays.

Visuals:

- KPI cards:
  - ICU stays
  - admissions with ICU flag
  - total ICU LOS days
  - median ICU LOS days
- Bar chart: ICU stays by admission type
- Bar chart: median ICU LOS by admission type
- Aggregate table from `icu_utilization_summary.csv`

## Page 4: Diagnosis Profile

Purpose: show the most common diagnosis categories in the demo subset.

Visuals:

- Bar chart: top 15 ICD codes by distinct admissions
- Table:
  - ICD code
  - ICD version
  - long title
  - diagnosis rows
  - distinct admissions
  - distinct patients
- Slicers:
  - ICD version
  - diagnosis title search

## Page 5: Lab Data Quality

Purpose: summarize lab volume and monitor missing numeric values.

Visuals:

- KPI cards:
  - total lab events
  - abnormal lab count
  - missing numeric value count
  - missing numeric value rate
- Bar chart: top lab items by event count
- Bar chart: top lab items by abnormal count
- Table:
  - item label
  - fluid
  - category
  - lab event count
  - abnormal rate
  - missing numeric value rate

## Page 6: Data Quality Monitor

Purpose: make data reliability visible, not hidden in code.

Visuals:

- KPI cards:
  - total checks
  - passed checks
  - warning checks
  - total issue count
- Matrix or table:
  - check name
  - table name
  - status
  - issue count
  - details
- Conditional formatting:
  - green for `PASS`
  - amber for `WARN`

## Dashboard Notes

- Do not present results as clinical recommendations.
- Mention that this uses the MIMIC-IV demo subset.
- Keep screenshots honest: use real outputs from this project only.
- Place final screenshots in a `screenshots/` folder before publishing to GitHub.
- Public GitHub data should come from `data/processed/` only. Do not publish row-level files from `data/generated/`.
