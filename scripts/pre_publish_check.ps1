param(
    [string]$GitExe = "git"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ForbiddenPathRegexes = @(
    "[A-Za-z]:[\\/](Users|Documents|Downloads|Desktop)",
    ("LEG" + "ION"),
    "Documents[\\/]Codex"
)
$IgnoreCheckPaths = @(
    "data/raw/example.csv.gz",
    "data/generated/row_level/example.csv",
    "sample.csv.gz",
    "sample.db",
    "sample.sqlite",
    ".venv/example",
    "venv/example",
    "__pycache__/example.pyc",
    ".pytest_cache/example",
    ".mypy_cache/example",
    ".ruff_cache/example"
)

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
    Write-Step "Scanning public files for local absolute paths"
    $PublicFiles = Get-ChildItem -Recurse -File |
        Where-Object {
            $_.FullName -notmatch "\\.git\\" -and
            $_.FullName -notmatch "\\data\\raw\\" -and
            $_.FullName -notmatch "\\data\\generated\\" -and
            $_.FullName -notmatch "__pycache__"
        }

    $PathMatches = @()
    foreach ($Pattern in $ForbiddenPathRegexes) {
        $PathMatches += Select-String -Path $PublicFiles.FullName -Pattern $Pattern -ErrorAction SilentlyContinue
    }

    if ($PathMatches.Count -gt 0) {
        $PathMatches | ForEach-Object {
            Write-Host "$($_.Path):$($_.LineNumber): $($_.Line)"
        }
        Fail "Local absolute path or machine-specific string found in public files."
    }
    Write-Host "OK no local path matches found"

    Write-Step "Checking .gitignore protections"
    foreach ($Path in $IgnoreCheckPaths) {
        & $GitExe check-ignore -q $Path
        if ($LASTEXITCODE -ne 0) {
            Fail ".gitignore does not protect expected path: $Path"
        }
        Write-Host "OK ignored: $Path"
    }

    Write-Step "Checking git add dry run"
    $DryRun = & $GitExe add --dry-run .
    $BlockedPatterns = @(
        "data/raw/",
        "data/generated/",
        ".csv.gz",
        "__pycache__"
    )

    foreach ($Line in $DryRun) {
        foreach ($Pattern in $BlockedPatterns) {
            if ($Line -like "*$Pattern*") {
                Fail "Unsafe file would be staged: $Line"
            }
        }
    }

    if ($DryRun) {
        Write-Host "Files that would be staged:"
        $DryRun | ForEach-Object { Write-Host $_ }
    }
    else {
        Write-Host "No files would be staged."
    }

    Write-Step "Pre-publish safety check completed"
    Write-Host "Repo is safe to commit/push from a data-governance perspective."
}
finally {
    Pop-Location
}
