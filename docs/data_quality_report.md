# Data Quality Report

## Scope

This report summarizes data quality checks for the MIMIC-IV Clinical Database Demo v2.2 workflow. The goal is to show whether the demo data can support reliable admission-level reporting.

## Checks Implemented

### Duplicate Checks

Checked for:

- duplicate `subject_id` in `patients`
- duplicate `hadm_id` in `admissions`

Why it matters: duplicated patient or admission identifiers can inflate counts and break one-row-per-admission reporting.

### Missing Values

Checked for:

- missing `subject_id` or `hadm_id`
- missing `admittime` or `dischtime`
- missing numeric lab values in `labevents.valuenum`

Why it matters: missing keys block joins, while missing dates block length-of-stay calculations.

### Invalid Dates

Checked for:

- unparseable admission timestamps
- discharge time before admission time

Why it matters: invalid timestamps create impossible length-of-stay values and unreliable outcome reporting.

### Orphan Keys

Checked for:

- admissions where `subject_id` is missing from `patients`
- diagnoses where `hadm_id` is missing from `admissions`
- labs where non-null `hadm_id` is missing from `admissions`
- transfers where `hadm_id` is missing from `admissions`
- ICU stays where `hadm_id` is missing from `admissions`
- lab events where `itemid` is missing from `d_labitems`

Why it matters: orphan keys indicate records that cannot be traced back to the expected reporting grain.

### Impossible Length of Stay

Checked for:

- negative hospital LOS
- long LOS flag using LOS >= 7 days

Why it matters: negative LOS is a data error; long LOS is a utilization segment for dashboard monitoring.

## Key Data Quality Findings

The generated file `data/processed/data_quality_checks.csv` is the source of truth for current check results after each pipeline run.

Expected interpretation:

- `PASS`: no issues found for the check.
- `WARN`: issues found or records worth monitoring.

Important nuance:

- Missing numeric lab values are not always errors. Some EHR lab events may be textual or categorical.
- Long LOS admissions are not data quality failures. They are flagged because they are analytically important for hospital operations.

## Reviewer Takeaway

The project demonstrates practical healthcare data quality thinking:

- confirm table grain before reporting
- validate joins before building dashboards
- separate true data errors from monitorable clinical/operational patterns
- document limitations instead of overstating conclusions
