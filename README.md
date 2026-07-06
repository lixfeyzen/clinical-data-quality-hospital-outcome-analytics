# Clinical Data Quality and Hospital Outcome Analytics

End-to-end clinical analytics portfolio project using the open **MIMIC-IV Clinical Database Demo v2.2** dataset from PhysioNet. The project validates EHR-style hospital data quality, models admission-level reporting outputs, and produces dashboard-ready CSVs across admissions, diagnoses, labs, transfers, and ICU stays.

This is a healthcare data analytics and data quality project. It is not medical advice and does not make clinical treatment recommendations.

## Business / Clinical Problem

Hospitals and analytics teams need reliable admission-level reporting before they can trust dashboards about outcomes, length of stay, ICU utilization, diagnosis mix, and lab activity.

This project answers:

- Are key hospital tables complete enough for reporting?
- Can admissions be linked cleanly to patients, diagnoses, labs, transfers, and ICU stays?
- What are the main admission-level outcome metrics in the demo dataset?
- What dashboard outputs would a BI analyst need for operational review?

## Dataset Source

- Dataset: MIMIC-IV Clinical Database Demo v2.2
- Source: PhysioNet open demo dataset
- Data type: de-identified EHR-style hospital data
- Scope used here: demo subset only, not the full MIMIC-IV database

Raw files are kept in `data/raw/` and ignored by Git. The public repository should include code, SQL, documentation, and processed aggregate outputs only.

## Data Governance

- Raw MIMIC-IV demo files are not committed to this repository.
- The MIMIC-IV demo dataset is de-identified and intended for research/education use.
- Public CSV outputs in `data/processed/` are aggregate, dashboard-ready files only.
- Row-level generated files are written locally to `data/generated/` and ignored by Git.
- This project is for analytics portfolio review, not clinical decision-making.

## Project Workflow

1. Load MIMIC-IV demo CSV or CSV.GZ raw files from `data/raw/`.
2. Validate required files and expected columns.
3. Build admission-level metrics:
   - length of stay
   - hospital mortality flag
   - ICU utilization flag
   - diagnosis count
   - lab event count
4. Run data quality checks:
   - duplicates
   - missing required values
   - invalid dates
   - orphan keys
   - impossible length of stay
5. Export clean dashboard-ready CSV files to `data/processed/`.
6. Define SQL views and Power BI dashboard pages for reviewer inspection.

## Key Metrics

Known results from the MIMIC-IV demo subset:

| Metric | Value |
|---|---:|
| Patients | 100 |
| Admissions | 275 |
| ICU stays | 140 |
| Diagnosis rows | 4,506 |
| Lab events | 107,727 |
| Hospital death admissions | 15 |
| Mortality rate | 5.45% |
| Median length of stay | 4.85 days |
| Long LOS admissions | 92 |
| Long LOS rate | 33.45% |

Long LOS is defined as hospital length of stay >= 7 days.

## Data Quality Checks

The pipeline produces `data/processed/data_quality_checks.csv` with checks for:

- duplicate patient IDs
- duplicate admission IDs
- missing admission IDs or patient IDs
- missing or invalid admission/discharge timestamps
- discharge before admission
- admissions without matching patient records
- diagnoses without matching admissions
- lab events without matching admissions
- lab item IDs missing from the lab dictionary
- transfers without matching admissions
- ICU stays without matching admissions
- lab events without numeric values

Some missing numeric lab values can be expected because EHR lab records may contain textual or non-numeric results. These are flagged for dashboard monitoring, not automatically treated as pipeline failures.

## Dashboard Outputs

The pipeline creates dashboard-ready CSV files:

| Output | Purpose |
|---|---|
| `hospital_kpis.csv` | Recruiter-friendly KPI summary |
| `admission_outcomes_summary.csv` | Aggregate admission outcomes by admission type |
| `diagnosis_profile.csv` | Aggregate ICD diagnosis frequency and coverage |
| `lab_summary.csv` | Lab item volume, abnormal flags, and missing numeric value rates |
| `icu_utilization_summary.csv` | Aggregate ICU utilization by admission type |
| `data_quality_checks.csv` | Data quality monitor table |

The pipeline also creates row-level local outputs in `data/generated/row_level/` for dashboard development. That folder is ignored by Git and should not be published.

## Tools Used

- Python
- pandas
- PostgreSQL SQL views
- Power BI dashboard specification
- Git/GitHub

## Repository Structure

```text
clinical-data-quality-hospital-outcome-analytics/
├── README.md
├── RUNNING.md
├── requirements.txt
├── .gitignore
├── docs/
│   ├── case_study.md
│   ├── dashboard_spec.md
│   └── data_quality_report.md
├── scripts/
│   └── build_outputs.py
├── sql/
│   └── 01_core_views_postgres.sql
└── data/
    ├── raw/          # ignored by Git
    ├── generated/    # ignored row-level local outputs
    └── processed/    # public aggregate outputs
```

## How to Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/build_outputs.py
```

See [RUNNING.md](RUNNING.md) for full setup and troubleshooting.

## Limitations

- Uses the MIMIC-IV demo subset only, so results are not representative of a hospital population.
- No machine learning is included because the demo sample is small.
- Metrics are descriptive analytics, not causal findings.
- Mortality uses the dataset field `hospital_expire_flag`; it should not be interpreted as a risk-adjusted clinical outcome.
- Lab abnormal flags depend on source data coding and should be validated before operational use.
- This project is designed for analytics portfolio review, not production clinical decision support.

## CV Bullets

- Built an end-to-end clinical analytics workflow using MIMIC-IV demo EHR data across admissions, diagnoses, labs, transfers, and ICU stays.
- Developed Python data validation and transformation pipeline producing admission-level and dashboard-ready hospital reporting outputs.
- Wrote PostgreSQL analytics views for length of stay, mortality flags, ICU utilization, diagnosis counts, lab summaries, and data quality checks.
- Documented healthcare data quality checks covering duplicates, missing values, invalid dates, orphan keys, and impossible length-of-stay records.
- Designed a Power BI dashboard specification for hospital outcomes, ICU utilization, diagnosis profile, lab quality, and data quality monitoring.

## Acceptance Checklist

- [x] README explains the project in under 60 seconds.
- [x] Dataset source is clearly identified as the open MIMIC-IV demo dataset.
- [x] Raw data is expected under `data/raw/` and protected by `.gitignore`.
- [x] Key metrics are visible near the top of the project.
- [x] Pipeline validates required files and columns.
- [x] Pipeline handles `.csv` and `.csv.gz` files.
- [x] Processed outputs are aggregate dashboard-ready CSV files.
- [x] Row-level generated outputs are excluded from Git.
- [x] SQL views are readable and reviewer-friendly.
- [x] Limitations are honest and do not overstate clinical claims.
- [x] No machine learning is claimed or added.
