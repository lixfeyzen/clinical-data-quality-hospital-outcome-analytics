# Running the Project

This project uses the open **MIMIC-IV Clinical Database Demo v2.2** dataset. Keep raw files local only. Do not commit raw MIMIC-IV files to GitHub.

## 1. Create a Virtual Environment

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Place Raw Dataset Files

Download or extract the MIMIC-IV demo dataset locally into:

```text
data/raw/
```

Expected examples:

```text
data/raw/mimic-iv-clinical-database-demo-2.2/hosp/admissions.csv.gz
data/raw/mimic-iv-clinical-database-demo-2.2/hosp/patients.csv.gz
data/raw/mimic-iv-clinical-database-demo-2.2/hosp/diagnoses_icd.csv.gz
data/raw/mimic-iv-clinical-database-demo-2.2/hosp/labevents.csv.gz
data/raw/mimic-iv-clinical-database-demo-2.2/icu/icustays.csv.gz
```

The pipeline searches recursively, so the top-level extracted folder name can vary.

## 3. Run the Pipeline

```powershell
python scripts/build_outputs.py
```

Optional custom paths:

```powershell
python scripts/build_outputs.py --raw-dir "path\to\raw" --output-dir "data\processed"
```

## 4. Run the Automated Local Workflow

This project includes two PowerShell scripts to reduce manual mistakes before publishing.

Run the pipeline and verify public aggregate outputs:

```powershell
.\scripts\run_portfolio_pipeline.ps1
```

Run the GitHub safety check before commit or push:

```powershell
.\scripts\pre_publish_check.ps1
```

The safety check verifies:

- no local machine paths are present in public files
- raw data and generated row-level outputs are ignored
- `.csv.gz`, local database files, virtual environments, and cache folders are ignored
- `git add --dry-run .` would not stage raw or row-level generated data

## 5. Inspect Outputs

Generated files:

```text
data/processed/hospital_kpis.csv
data/processed/admission_outcomes_summary.csv
data/processed/diagnosis_profile.csv
data/processed/lab_summary.csv
data/processed/icu_utilization_summary.csv
data/processed/data_quality_checks.csv
```

The script also writes local row-level development files to:

```text
data/generated/row_level/admissions_summary.csv
data/generated/row_level/icu_utilization.csv
```

`data/generated/` is ignored by Git. Do not publish those files.

Quick checks:

```powershell
Get-ChildItem data\processed
Import-Csv data\processed\hospital_kpis.csv | Format-Table
Import-Csv data\processed\data_quality_checks.csv | Format-Table
```

## Common Troubleshooting

### `Raw data directory not found`

Create `data/raw/` and extract the MIMIC-IV demo zip there, or pass `--raw-dir`.

### `Missing required raw file`

Confirm the demo files are extracted and still named like `admissions.csv.gz`, `patients.csv.gz`, `labevents.csv.gz`, and `icustays.csv.gz`.

### `missing required columns`

The script expects MIMIC-IV demo v2.2 style columns. If you use a different version, inspect the column names before modifying the script.

### `ModuleNotFoundError: pandas`

Activate the virtual environment and run:

```powershell
pip install -r requirements.txt
```

### Power BI cannot load a CSV

Use the aggregate files in `data/processed/`, not raw files from `data/raw/` or row-level files from `data/generated/`. The public processed outputs are dashboard-ready and safer for GitHub.
