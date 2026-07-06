"""Build dashboard-ready outputs from the MIMIC-IV Clinical Database Demo.

This script expects the open MIMIC-IV demo dataset files under data/raw/.
It reads .csv or .csv.gz files recursively, validates required inputs, and
creates aggregate CSV outputs safe for a public portfolio repository.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_GENERATED_DIR = PROJECT_ROOT / "data" / "generated" / "row_level"
LONG_LOS_DAYS = 7


@dataclass(frozen=True)
class InputFile:
    key: str
    preferred_folder: str
    required_columns: tuple[str, ...]


REQUIRED_FILES: tuple[InputFile, ...] = (
    InputFile(
        "patients",
        "hosp",
        ("subject_id", "gender", "anchor_age", "anchor_year", "anchor_year_group"),
    ),
    InputFile(
        "admissions",
        "hosp",
        (
            "subject_id",
            "hadm_id",
            "admittime",
            "dischtime",
            "admission_type",
            "admission_location",
            "discharge_location",
            "insurance",
            "language",
            "marital_status",
            "race",
            "hospital_expire_flag",
        ),
    ),
    InputFile("diagnoses_icd", "hosp", ("subject_id", "hadm_id", "seq_num", "icd_code", "icd_version")),
    InputFile("d_icd_diagnoses", "hosp", ("icd_code", "icd_version", "long_title")),
    InputFile("labevents", "hosp", ("subject_id", "hadm_id", "itemid", "charttime", "valuenum", "flag")),
    InputFile("d_labitems", "hosp", ("itemid", "label", "fluid", "category")),
    InputFile("transfers", "hosp", ("subject_id", "hadm_id", "transfer_id", "eventtype", "intime", "outtime")),
    InputFile("icustays", "icu", ("subject_id", "hadm_id", "stay_id", "intime", "outtime", "los")),
)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build dashboard-ready aggregate outputs from MIMIC-IV demo raw files."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help="Folder containing extracted MIMIC-IV demo raw files. Default: data/raw",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder where public aggregate CSV outputs will be written. Default: data/processed",
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=DEFAULT_GENERATED_DIR,
        help="Ignored folder for row-level generated outputs. Default: data/generated/row_level",
    )
    return parser.parse_args()


def normalized_table_name(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".csv.gz"):
        return name.removesuffix(".csv.gz")
    if name.endswith(".csv"):
        return name.removesuffix(".csv")
    return path.stem.lower()


def find_input_files(raw_dir: Path) -> dict[str, Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {raw_dir}\n"
            "Extract the MIMIC-IV demo zip into data/raw/ or pass --raw-dir."
        )

    candidates = [
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and (path.name.lower().endswith(".csv") or path.name.lower().endswith(".csv.gz"))
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No .csv or .csv.gz files found under {raw_dir}\n"
            "Expected files such as hosp/admissions.csv.gz and icu/icustays.csv.gz."
        )

    resolved: dict[str, Path] = {}
    for spec in REQUIRED_FILES:
        matches = [path for path in candidates if normalized_table_name(path) == spec.key]
        if not matches:
            raise FileNotFoundError(
                f"Missing required raw file for table '{spec.key}'.\n"
                f"Expected {spec.key}.csv or {spec.key}.csv.gz somewhere under {raw_dir}."
            )

        preferred = [
            path for path in matches if spec.preferred_folder.lower() in [part.lower() for part in path.parts]
        ]
        selected = sorted(preferred or matches, key=lambda item: len(str(item)))[0]
        resolved[spec.key] = selected

    return resolved


def load_table(spec: InputFile, path: Path) -> pd.DataFrame:
    logging.info("Loading %-16s from %s", spec.key, path)
    df = pd.read_csv(path, low_memory=False)
    missing_columns = [column for column in spec.required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Raw file {path} is missing required columns for '{spec.key}': {missing_columns}"
        )
    return df


def parse_datetime_column(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(df[column], errors="coerce")


def percent(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return round(float(numerator) / float(denominator) * 100, 2)


def build_admissions_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    admissions = tables["admissions"].copy()
    patients = tables["patients"].copy()
    diagnoses = tables["diagnoses_icd"].copy()
    labs = tables["labevents"].copy()
    icu = tables["icustays"].copy()

    admissions["admittime"] = parse_datetime_column(admissions, "admittime")
    admissions["dischtime"] = parse_datetime_column(admissions, "dischtime")
    admissions["los_days"] = (
        (admissions["dischtime"] - admissions["admittime"]).dt.total_seconds() / 86400
    ).round(2)
    admissions["mortality_flag"] = admissions["hospital_expire_flag"].fillna(0).astype(int)
    admissions["long_los_flag"] = (admissions["los_days"] >= LONG_LOS_DAYS).astype(int)

    patient_cols = ["subject_id", "gender", "anchor_age", "anchor_year", "anchor_year_group"]
    summary = admissions.merge(patients[patient_cols], on="subject_id", how="left")

    diagnosis_counts = (
        diagnoses.groupby("hadm_id", dropna=False)
        .size()
        .reset_index(name="diagnosis_count")
    )
    summary = summary.merge(diagnosis_counts, on="hadm_id", how="left")

    lab_counts = (
        labs.groupby("hadm_id", dropna=True)
        .agg(
            lab_event_count=("itemid", "size"),
            abnormal_lab_count=("flag", lambda series: series.fillna("").str.lower().eq("abnormal").sum()),
            missing_lab_value_count=("valuenum", lambda series: series.isna().sum()),
        )
        .reset_index()
    )
    summary = summary.merge(lab_counts, on="hadm_id", how="left")

    icu["intime"] = parse_datetime_column(icu, "intime")
    icu["outtime"] = parse_datetime_column(icu, "outtime")
    icu_summary = (
        icu.groupby("hadm_id", dropna=True)
        .agg(
            icu_stay_count=("stay_id", "nunique"),
            first_icu_intime=("intime", "min"),
            last_icu_outtime=("outtime", "max"),
            total_icu_los_days=("los", "sum"),
        )
        .reset_index()
    )
    summary = summary.merge(icu_summary, on="hadm_id", how="left")
    summary["icu_flag"] = summary["icu_stay_count"].fillna(0).gt(0).astype(int)

    fill_zero_cols = [
        "diagnosis_count",
        "lab_event_count",
        "abnormal_lab_count",
        "missing_lab_value_count",
        "icu_stay_count",
        "total_icu_los_days",
    ]
    for column in fill_zero_cols:
        summary[column] = summary[column].fillna(0)

    output_columns = [
        "subject_id",
        "hadm_id",
        "gender",
        "anchor_age",
        "admittime",
        "dischtime",
        "los_days",
        "long_los_flag",
        "mortality_flag",
        "icu_flag",
        "icu_stay_count",
        "total_icu_los_days",
        "diagnosis_count",
        "lab_event_count",
        "abnormal_lab_count",
        "missing_lab_value_count",
        "admission_type",
        "admission_location",
        "discharge_location",
        "insurance",
        "language",
        "marital_status",
        "race",
        "anchor_year",
        "anchor_year_group",
        "first_icu_intime",
        "last_icu_outtime",
    ]
    return summary[output_columns].sort_values(["subject_id", "hadm_id"])


def build_diagnosis_profile(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    diagnoses = tables["diagnoses_icd"].copy()
    dictionary = tables["d_icd_diagnoses"].copy()
    profile = (
        diagnoses.merge(dictionary, on=["icd_code", "icd_version"], how="left")
        .groupby(["icd_code", "icd_version", "long_title"], dropna=False)
        .agg(
            diagnosis_rows=("hadm_id", "size"),
            distinct_admissions=("hadm_id", "nunique"),
            distinct_patients=("subject_id", "nunique"),
        )
        .reset_index()
        .sort_values(["distinct_admissions", "diagnosis_rows"], ascending=False)
    )
    return profile


def build_admission_outcomes_summary(admissions_summary: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        admissions_summary.groupby("admission_type", dropna=False)
        .agg(
            admissions=("hadm_id", "nunique"),
            hospital_death_admissions=("mortality_flag", "sum"),
            long_los_admissions=("long_los_flag", "sum"),
            icu_admissions=("icu_flag", "sum"),
            median_los_days=("los_days", "median"),
            average_los_days=("los_days", "mean"),
            diagnosis_rows=("diagnosis_count", "sum"),
            lab_events=("lab_event_count", "sum"),
        )
        .reset_index()
    )
    grouped["mortality_rate_pct"] = grouped.apply(
        lambda row: percent(row["hospital_death_admissions"], row["admissions"]), axis=1
    )
    grouped["long_los_rate_pct"] = grouped.apply(
        lambda row: percent(row["long_los_admissions"], row["admissions"]), axis=1
    )
    grouped["icu_admission_rate_pct"] = grouped.apply(
        lambda row: percent(row["icu_admissions"], row["admissions"]), axis=1
    )
    grouped["median_los_days"] = grouped["median_los_days"].round(2)
    grouped["average_los_days"] = grouped["average_los_days"].round(2)
    return grouped.sort_values("admissions", ascending=False)


def build_lab_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    labs = tables["labevents"].copy()
    lab_items = tables["d_labitems"].copy()
    labs["charttime"] = parse_datetime_column(labs, "charttime")
    summary = (
        labs.merge(lab_items, on="itemid", how="left")
        .groupby(["itemid", "label", "fluid", "category"], dropna=False)
        .agg(
            lab_event_count=("itemid", "size"),
            distinct_admissions=("hadm_id", "nunique"),
            distinct_patients=("subject_id", "nunique"),
            abnormal_count=("flag", lambda series: series.fillna("").str.lower().eq("abnormal").sum()),
            missing_numeric_value_count=("valuenum", lambda series: series.isna().sum()),
            first_charttime=("charttime", "min"),
            last_charttime=("charttime", "max"),
        )
        .reset_index()
    )
    summary["abnormal_rate_pct"] = summary.apply(
        lambda row: percent(row["abnormal_count"], row["lab_event_count"]), axis=1
    )
    summary["missing_numeric_value_rate_pct"] = summary.apply(
        lambda row: percent(row["missing_numeric_value_count"], row["lab_event_count"]), axis=1
    )
    return summary.sort_values("lab_event_count", ascending=False)


def build_icu_utilization(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    icu = tables["icustays"].copy()
    admissions = tables["admissions"][["hadm_id", "admission_type", "hospital_expire_flag"]].copy()
    icu["intime"] = parse_datetime_column(icu, "intime")
    icu["outtime"] = parse_datetime_column(icu, "outtime")
    output = icu.merge(admissions, on="hadm_id", how="left")
    output["icu_los_days"] = output["los"].round(2)
    columns = [
        "subject_id",
        "hadm_id",
        "stay_id",
        "intime",
        "outtime",
        "icu_los_days",
        "admission_type",
        "hospital_expire_flag",
    ]
    return output[columns].sort_values(["subject_id", "hadm_id", "intime"])


def build_icu_utilization_summary(icu_utilization: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        icu_utilization.groupby("admission_type", dropna=False)
        .agg(
            icu_stays=("stay_id", "nunique"),
            distinct_admissions=("hadm_id", "nunique"),
            median_icu_los_days=("icu_los_days", "median"),
            average_icu_los_days=("icu_los_days", "mean"),
            hospital_death_admissions=("hospital_expire_flag", "sum"),
        )
        .reset_index()
    )
    grouped["median_icu_los_days"] = grouped["median_icu_los_days"].round(2)
    grouped["average_icu_los_days"] = grouped["average_icu_los_days"].round(2)
    grouped["icu_mortality_rate_pct"] = grouped.apply(
        lambda row: percent(row["hospital_death_admissions"], row["distinct_admissions"]), axis=1
    )
    return grouped.sort_values("icu_stays", ascending=False)


def add_quality_row(rows: list[dict[str, object]], check_name: str, table_name: str, issue_count: int, details: str) -> None:
    rows.append(
        {
            "check_name": check_name,
            "table_name": table_name,
            "status": "PASS" if issue_count == 0 else "WARN",
            "issue_count": int(issue_count),
            "details": details,
        }
    )


def build_data_quality_checks(tables: dict[str, pd.DataFrame], admissions_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    patients = tables["patients"]
    admissions = tables["admissions"].copy()
    diagnoses = tables["diagnoses_icd"]
    labs = tables["labevents"]
    lab_items = tables["d_labitems"]
    transfers = tables["transfers"]
    icu = tables["icustays"]

    admissions["admittime_parsed"] = parse_datetime_column(admissions, "admittime")
    admissions["dischtime_parsed"] = parse_datetime_column(admissions, "dischtime")

    add_quality_row(rows, "duplicate_subject_id", "patients", patients.duplicated("subject_id").sum(), "Duplicate patient IDs.")
    add_quality_row(rows, "duplicate_hadm_id", "admissions", admissions.duplicated("hadm_id").sum(), "Duplicate admission IDs.")
    add_quality_row(rows, "missing_required_ids", "admissions", admissions[["subject_id", "hadm_id"]].isna().any(axis=1).sum(), "Missing subject_id or hadm_id.")
    add_quality_row(rows, "missing_admission_dates", "admissions", admissions[["admittime", "dischtime"]].isna().any(axis=1).sum(), "Missing admission or discharge timestamps.")
    add_quality_row(rows, "invalid_admission_dates", "admissions", admissions[["admittime_parsed", "dischtime_parsed"]].isna().any(axis=1).sum(), "Unparseable admission or discharge timestamps.")
    add_quality_row(rows, "impossible_negative_los", "admissions", (admissions["dischtime_parsed"] < admissions["admittime_parsed"]).sum(), "Discharge timestamp before admission timestamp.")
    add_quality_row(rows, "orphan_admission_subject_id", "admissions", (~admissions["subject_id"].isin(patients["subject_id"])).sum(), "Admissions with subject_id not found in patients.")
    add_quality_row(rows, "orphan_diagnosis_hadm_id", "diagnoses_icd", (~diagnoses["hadm_id"].isin(admissions["hadm_id"])).sum(), "Diagnosis rows with hadm_id not found in admissions.")
    lab_hadm = labs["hadm_id"].dropna()
    add_quality_row(rows, "orphan_lab_hadm_id", "labevents", (~lab_hadm.isin(admissions["hadm_id"])).sum(), "Lab rows with non-null hadm_id not found in admissions.")
    add_quality_row(rows, "orphan_lab_itemid", "labevents", (~labs["itemid"].isin(lab_items["itemid"])).sum(), "Lab rows with itemid not found in d_labitems.")
    add_quality_row(rows, "orphan_transfer_hadm_id", "transfers", (~transfers["hadm_id"].dropna().isin(admissions["hadm_id"])).sum(), "Transfer rows with hadm_id not found in admissions.")
    add_quality_row(rows, "orphan_icu_hadm_id", "icustays", (~icu["hadm_id"].isin(admissions["hadm_id"])).sum(), "ICU stays with hadm_id not found in admissions.")
    add_quality_row(rows, "missing_lab_numeric_value", "labevents", labs["valuenum"].isna().sum(), "Lab events without numeric valuenum. Some lab events are textual by design.")
    add_quality_row(rows, "long_los_threshold_check", "admissions_summary", admissions_summary["long_los_flag"].sum(), f"Admissions with LOS >= {LONG_LOS_DAYS} days; monitor as utilization/outcome segment, not as data error.")

    return pd.DataFrame(rows)


def build_hospital_kpis(tables: dict[str, pd.DataFrame], admissions_summary: pd.DataFrame) -> pd.DataFrame:
    admissions_count = len(tables["admissions"])
    hospital_deaths = int(admissions_summary["mortality_flag"].sum())
    long_los_count = int(admissions_summary["long_los_flag"].sum())
    kpis = [
        ("patients", len(tables["patients"]), "Distinct demo patients."),
        ("admissions", admissions_count, "Hospital admissions."),
        ("icu_stays", len(tables["icustays"]), "ICU stay rows."),
        ("diagnosis_rows", len(tables["diagnoses_icd"]), "Diagnosis ICD rows."),
        ("lab_events", len(tables["labevents"]), "Lab event rows."),
        ("hospital_death_admissions", hospital_deaths, "Admissions with hospital_expire_flag = 1."),
        ("mortality_rate_pct", percent(hospital_deaths, admissions_count), "Hospital death admissions divided by admissions."),
        ("median_los_days", round(float(admissions_summary["los_days"].median()), 2), "Median hospital length of stay in days."),
        ("long_los_admissions", long_los_count, f"Admissions with LOS >= {LONG_LOS_DAYS} days."),
        ("long_los_rate_pct", percent(long_los_count, admissions_count), f"LOS >= {LONG_LOS_DAYS} days divided by admissions."),
        ("icu_admissions", int(admissions_summary["icu_flag"].sum()), "Admissions linked to one or more ICU stays."),
    ]
    return pd.DataFrame(kpis, columns=["metric", "value", "definition"])


def write_outputs(output_dir: Path, outputs: dict[str, pd.DataFrame]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, df in outputs.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        logging.info("Wrote %-28s rows=%s", path.relative_to(PROJECT_ROOT), f"{len(df):,}")


def remove_stale_public_row_level_outputs(output_dir: Path) -> None:
    for filename in ("admissions_summary.csv", "icu_utilization.csv"):
        path = output_dir / filename
        if path.exists():
            path.unlink()
            logging.info("Removed row-level public output %s", path.relative_to(PROJECT_ROOT))


def main() -> int:
    configure_logging()
    args = parse_args()
    raw_dir = args.raw_dir.resolve()
    output_dir = args.output_dir.resolve()

    try:
        input_paths = find_input_files(raw_dir)
        for key, path in input_paths.items():
            logging.info("Resolved %-16s -> %s", key, path)

        specs_by_key = {spec.key: spec for spec in REQUIRED_FILES}
        tables = {key: load_table(specs_by_key[key], path) for key, path in input_paths.items()}

        admissions_summary = build_admissions_summary(tables)
        icu_utilization = build_icu_utilization(tables)
        outputs = {
            "hospital_kpis": build_hospital_kpis(tables, admissions_summary),
            "admission_outcomes_summary": build_admission_outcomes_summary(admissions_summary),
            "diagnosis_profile": build_diagnosis_profile(tables),
            "lab_summary": build_lab_summary(tables),
            "icu_utilization_summary": build_icu_utilization_summary(icu_utilization),
            "data_quality_checks": build_data_quality_checks(tables, admissions_summary),
        }
        remove_stale_public_row_level_outputs(output_dir)
        write_outputs(output_dir, outputs)
        generated_outputs = {
            "admissions_summary": admissions_summary,
            "icu_utilization": icu_utilization,
        }
        write_outputs(args.generated_dir.resolve(), generated_outputs)
        logging.info("Pipeline complete. Outputs are dashboard-ready aggregate CSV files.")
        return 0
    except Exception as exc:
        logging.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
