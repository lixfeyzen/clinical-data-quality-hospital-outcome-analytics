# Case Study: Clinical Data Quality and Hospital Outcome Analytics

## Problem

Clinical reporting depends on reliable joins across patient, admission, diagnosis, lab, transfer, and ICU tables. Before a dashboard can be trusted, an analyst needs to verify that core records are complete, keys connect correctly, timestamps make sense, and outcome metrics are defined consistently.

This project uses the open MIMIC-IV Clinical Database Demo v2.2 dataset to build a small but realistic hospital analytics workflow.

## Approach

The workflow focuses on descriptive analytics and data quality, not prediction.

Steps:

1. Load MIMIC-IV demo raw files from `data/raw/`.
2. Validate required tables and columns.
3. Create admission-level reporting fields:
   - length of stay
   - long LOS flag
   - hospital mortality flag
   - ICU flag
   - diagnosis count
   - lab event count
4. Produce dashboard-ready aggregate CSV outputs.
5. Define SQL views that mirror the analytical logic for PostgreSQL review.
6. Document data quality checks and dashboard design.

## Analysis

The analysis centers on admission-level hospital outcomes and data readiness:

- Admission volume and patient coverage
- Hospital mortality count and rate
- Length-of-stay distribution
- Long LOS admissions using LOS >= 7 days
- ICU stay linkage to admissions
- Diagnosis frequency by ICD code
- Lab volume, abnormal flags, and missing numeric values
- Data quality checks across keys and timestamps

## Findings

Known results from the demo subset:

- 100 patients
- 275 admissions
- 140 ICU stays
- 4,506 diagnosis rows
- 107,727 lab events
- 15 hospital death admissions
- 5.45% hospital mortality rate
- 4.85 day median length of stay
- 92 long LOS admissions
- 33.45% long LOS rate

These findings show that the demo dataset is large enough to demonstrate healthcare analytics workflow skills, but too small for reliable clinical modeling.

## Limitations

- The dataset is a demo subset and is not representative of the full MIMIC-IV population.
- Metrics are descriptive and should not be interpreted as clinical recommendations.
- No risk adjustment is performed.
- No machine learning is included because the sample is small.
- Lab abnormal rates depend on source flags and should be validated with clinical context before operational use.
- Public portfolio outputs should remain aggregate or transformed. Raw MIMIC-IV files should not be committed.

## Recommendations

- Use `admission_outcomes_summary.csv` as the public admission outcomes table.
- Use `hospital_kpis.csv` for an executive overview page.
- Use `data_quality_checks.csv` as a visible data reliability monitor.
- Add dashboard screenshots after building Power BI pages.
- Keep the project positioned as clinical data quality and hospital outcome analytics, not predictive medicine.
