/*
Core PostgreSQL views for the MIMIC-IV Clinical Database Demo v2.2.

Assumptions:
- Raw demo tables are loaded into schemas named mimiciv_hosp and mimiciv_icu.
- These views are for analytics and portfolio review, not clinical decision support.
- The public repository should not include raw MIMIC-IV files.
*/

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.admission_length_of_stay AS
SELECT
    a.subject_id,
    a.hadm_id,
    a.admittime,
    a.dischtime,
    ROUND(EXTRACT(EPOCH FROM (a.dischtime - a.admittime)) / 86400.0, 2) AS los_days,
    CASE
        WHEN a.dischtime < a.admittime THEN 1
        ELSE 0
    END AS negative_los_flag,
    CASE
        WHEN EXTRACT(EPOCH FROM (a.dischtime - a.admittime)) / 86400.0 >= 7 THEN 1
        ELSE 0
    END AS long_los_flag
FROM mimiciv_hosp.admissions AS a;

CREATE OR REPLACE VIEW analytics.admission_mortality_flags AS
SELECT
    a.subject_id,
    a.hadm_id,
    COALESCE(a.hospital_expire_flag, 0) AS mortality_flag
FROM mimiciv_hosp.admissions AS a;

CREATE OR REPLACE VIEW analytics.admission_icu_flags AS
SELECT
    a.subject_id,
    a.hadm_id,
    CASE WHEN COUNT(i.stay_id) > 0 THEN 1 ELSE 0 END AS icu_flag,
    COUNT(DISTINCT i.stay_id) AS icu_stay_count,
    MIN(i.intime) AS first_icu_intime,
    MAX(i.outtime) AS last_icu_outtime,
    ROUND(COALESCE(SUM(i.los), 0)::numeric, 2) AS total_icu_los_days
FROM mimiciv_hosp.admissions AS a
LEFT JOIN mimiciv_icu.icustays AS i
    ON a.hadm_id = i.hadm_id
GROUP BY
    a.subject_id,
    a.hadm_id;

CREATE OR REPLACE VIEW analytics.admission_diagnosis_counts AS
SELECT
    a.subject_id,
    a.hadm_id,
    COUNT(d.icd_code) AS diagnosis_count
FROM mimiciv_hosp.admissions AS a
LEFT JOIN mimiciv_hosp.diagnoses_icd AS d
    ON a.hadm_id = d.hadm_id
GROUP BY
    a.subject_id,
    a.hadm_id;

CREATE OR REPLACE VIEW analytics.admission_lab_summary AS
SELECT
    a.subject_id,
    a.hadm_id,
    COUNT(l.itemid) AS lab_event_count,
    SUM(CASE WHEN LOWER(COALESCE(l.flag, '')) = 'abnormal' THEN 1 ELSE 0 END) AS abnormal_lab_count,
    SUM(CASE WHEN l.valuenum IS NULL THEN 1 ELSE 0 END) AS missing_numeric_lab_value_count,
    MIN(l.charttime) AS first_lab_charttime,
    MAX(l.charttime) AS last_lab_charttime
FROM mimiciv_hosp.admissions AS a
LEFT JOIN mimiciv_hosp.labevents AS l
    ON a.hadm_id = l.hadm_id
GROUP BY
    a.subject_id,
    a.hadm_id;

CREATE OR REPLACE VIEW analytics.admissions_summary AS
SELECT
    a.subject_id,
    a.hadm_id,
    p.gender,
    p.anchor_age,
    a.admittime,
    a.dischtime,
    los.los_days,
    los.long_los_flag,
    mort.mortality_flag,
    icu.icu_flag,
    icu.icu_stay_count,
    icu.total_icu_los_days,
    diag.diagnosis_count,
    labs.lab_event_count,
    labs.abnormal_lab_count,
    labs.missing_numeric_lab_value_count,
    a.admission_type,
    a.admission_location,
    a.discharge_location,
    a.insurance,
    a.language,
    a.marital_status,
    a.race
FROM mimiciv_hosp.admissions AS a
LEFT JOIN mimiciv_hosp.patients AS p
    ON a.subject_id = p.subject_id
LEFT JOIN analytics.admission_length_of_stay AS los
    ON a.hadm_id = los.hadm_id
LEFT JOIN analytics.admission_mortality_flags AS mort
    ON a.hadm_id = mort.hadm_id
LEFT JOIN analytics.admission_icu_flags AS icu
    ON a.hadm_id = icu.hadm_id
LEFT JOIN analytics.admission_diagnosis_counts AS diag
    ON a.hadm_id = diag.hadm_id
LEFT JOIN analytics.admission_lab_summary AS labs
    ON a.hadm_id = labs.hadm_id;

CREATE OR REPLACE VIEW analytics.diagnosis_profile AS
SELECT
    d.icd_code,
    d.icd_version,
    dd.long_title,
    COUNT(*) AS diagnosis_rows,
    COUNT(DISTINCT d.hadm_id) AS distinct_admissions,
    COUNT(DISTINCT d.subject_id) AS distinct_patients
FROM mimiciv_hosp.diagnoses_icd AS d
LEFT JOIN mimiciv_hosp.d_icd_diagnoses AS dd
    ON d.icd_code = dd.icd_code
    AND d.icd_version = dd.icd_version
GROUP BY
    d.icd_code,
    d.icd_version,
    dd.long_title;

CREATE OR REPLACE VIEW analytics.lab_item_summary AS
SELECT
    l.itemid,
    li.label,
    li.fluid,
    li.category,
    COUNT(*) AS lab_event_count,
    COUNT(DISTINCT l.hadm_id) AS distinct_admissions,
    COUNT(DISTINCT l.subject_id) AS distinct_patients,
    SUM(CASE WHEN LOWER(COALESCE(l.flag, '')) = 'abnormal' THEN 1 ELSE 0 END) AS abnormal_count,
    SUM(CASE WHEN l.valuenum IS NULL THEN 1 ELSE 0 END) AS missing_numeric_value_count
FROM mimiciv_hosp.labevents AS l
LEFT JOIN mimiciv_hosp.d_labitems AS li
    ON l.itemid = li.itemid
GROUP BY
    l.itemid,
    li.label,
    li.fluid,
    li.category;

CREATE OR REPLACE VIEW analytics.data_quality_checks AS
SELECT
    'duplicate_subject_id' AS check_name,
    'patients' AS table_name,
    COUNT(*) AS issue_count,
    'Duplicate patient IDs' AS details
FROM (
    SELECT subject_id
    FROM mimiciv_hosp.patients
    GROUP BY subject_id
    HAVING COUNT(*) > 1
) AS q

UNION ALL

SELECT
    'duplicate_hadm_id',
    'admissions',
    COUNT(*),
    'Duplicate admission IDs'
FROM (
    SELECT hadm_id
    FROM mimiciv_hosp.admissions
    GROUP BY hadm_id
    HAVING COUNT(*) > 1
) AS q

UNION ALL

SELECT
    'invalid_or_missing_admission_dates',
    'admissions',
    COUNT(*),
    'Missing timestamps or discharge before admission'
FROM mimiciv_hosp.admissions
WHERE admittime IS NULL
    OR dischtime IS NULL
    OR dischtime < admittime

UNION ALL

SELECT
    'orphan_admission_subject_id',
    'admissions',
    COUNT(*),
    'Admissions with subject_id not found in patients'
FROM mimiciv_hosp.admissions AS a
LEFT JOIN mimiciv_hosp.patients AS p
    ON a.subject_id = p.subject_id
WHERE p.subject_id IS NULL

UNION ALL

SELECT
    'orphan_diagnosis_hadm_id',
    'diagnoses_icd',
    COUNT(*),
    'Diagnosis rows with hadm_id not found in admissions'
FROM mimiciv_hosp.diagnoses_icd AS d
LEFT JOIN mimiciv_hosp.admissions AS a
    ON d.hadm_id = a.hadm_id
WHERE a.hadm_id IS NULL

UNION ALL

SELECT
    'orphan_lab_hadm_id',
    'labevents',
    COUNT(*),
    'Lab rows with non-null hadm_id not found in admissions'
FROM mimiciv_hosp.labevents AS l
LEFT JOIN mimiciv_hosp.admissions AS a
    ON l.hadm_id = a.hadm_id
WHERE l.hadm_id IS NOT NULL
    AND a.hadm_id IS NULL

UNION ALL

SELECT
    'orphan_icu_hadm_id',
    'icustays',
    COUNT(*),
    'ICU stays with hadm_id not found in admissions'
FROM mimiciv_icu.icustays AS i
LEFT JOIN mimiciv_hosp.admissions AS a
    ON i.hadm_id = a.hadm_id
WHERE a.hadm_id IS NULL;
