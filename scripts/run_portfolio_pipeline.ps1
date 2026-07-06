param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ProcessedDir = Join-Path $ProjectRoot "data\processed"
$RequiredOutputs = @(
    "hospital_kpis.csv",
    "admission_outcomes_summary.csv",
    "diagnosis_profile.csv",
    "lab_summary.csv",
    "icu_utilization_summary.csv",
    "data_quality_checks.csv"
)
$ForbiddenPublicColumns = @("subject_id", "hadm_id", "stay_id")

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Fail {
    param([string]$Message)
    throw "[FAILED] $Message"
}

Push-Location $ProjectRoot
try {
    Write-Step "Running portfolio output pipeline"
    & $PythonExe "scripts\build_outputs.py"
    if ($LASTEXITCODE -ne 0) {
        Fail "Pipeline exited with code $LASTEXITCODE."
    }

    Write-Step "Checking required aggregate outputs"
    foreach ($FileName in $RequiredOutputs) {
        $Path = Join-Path $ProcessedDir $FileName
        if (-not (Test-Path $Path)) {
            Fail "Missing required output: data\processed\$FileName"
        }
        $Item = Get-Item $Path
        if ($Item.Length -le 0) {
            Fail "Output file is empty: data\processed\$FileName"
        }
        Write-Host "OK data\processed\$FileName ($($Item.Length) bytes)"
    }

    Write-Step "Checking public outputs for row-level identifiers"
    $PublicCsvFiles = Get-ChildItem -Path $ProcessedDir -Filter "*.csv" -File
    foreach ($Csv in $PublicCsvFiles) {
        $Header = Get-Content -LiteralPath $Csv.FullName -TotalCount 1
        $Columns = $Header -split ","
        $Found = @($Columns | Where-Object { $ForbiddenPublicColumns -contains $_ })
        if ($Found.Count -gt 0) {
            Fail "Public output contains identifier column(s): $($Csv.Name) -> $($Found -join ', ')"
        }
        Write-Host "OK $($Csv.Name) has no subject_id/hadm_id/stay_id columns"
    }

    Write-Step "Pipeline automation completed"
    Write-Host "All public processed outputs are present and aggregate-safe."
}
finally {
    Pop-Location
}
