Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$DbPath = "v2_4_rc_test.db"
$FinancialCsv = "tests/sample_data/historical/financial_snapshots_valid.csv"
$ReportPath = "reports/v2_4_rc_validation.md"
$QualificationJson = "reports/backtest_qualification.json"
$LogPath = "reports/v2_4_rc_validation.log"

function Invoke-RCStep {
    param(
        [string]$Name,
        [string[]]$Command,
        [string]$LogPath
    )

    Write-Host "[$Name] $($Command -join ' ')"
    Add-Content -LiteralPath $LogPath -Value ""
    Add-Content -LiteralPath $LogPath -Value "[$Name] $($Command -join ' ')"

    $CommandArgs = @()
    if ($Command.Length -gt 1) {
        $CommandArgs = $Command[1..($Command.Length - 1)]
    }

    $TempOutput = [System.IO.Path]::GetTempFileName()
    try {
        & $Command[0] @CommandArgs > $TempOutput 2>&1
        $ExitCode = $LASTEXITCODE
        Get-Content -LiteralPath $TempOutput | Add-Content -LiteralPath $LogPath
    }
    finally {
        if (Test-Path -LiteralPath $TempOutput) {
            Remove-Item -LiteralPath $TempOutput
        }
    }

    if ($ExitCode -eq 0) {
        Add-Content -LiteralPath $LogPath -Value "[$Name] status=pass"
        return "pass"
    }
    Add-Content -LiteralPath $LogPath -Value "[$Name] status=fail(exit_code=$ExitCode)"
    return "fail(exit_code=$ExitCode)"
}

if (Test-Path -LiteralPath $DbPath) {
    Remove-Item -LiteralPath $DbPath
}

if (Test-Path -LiteralPath $LogPath) {
    Remove-Item -LiteralPath $LogPath
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null
Add-Content -LiteralPath $LogPath -Value "# v2.4 RC Validation Log"

$ImportStatus = Invoke-RCStep "Import" @(
    ".venv\Scripts\python.exe",
    "historical_import.py",
    "--type",
    "financial",
    "--file",
    $FinancialCsv,
    "--db",
    $DbPath
) $LogPath

$GeneratorStatus = Invoke-RCStep "Generator" @(
    ".venv\Scripts\python.exe",
    "historical_generate_sap.py",
    "--db",
    $DbPath
) $LogPath

$BacktestStatus = Invoke-RCStep "Backtest" @(
    ".venv\Scripts\python.exe",
    "backtest.py",
    "--snapshot-source",
    "repository",
    "--snapshot-db",
    $DbPath
) $LogPath

$StrategyComparisonStatus = Invoke-RCStep "StrategyComparison" @(
    ".venv\Scripts\python.exe",
    "strategy_compare.py",
    "--snapshot-source",
    "repository",
    "--snapshot-db",
    $DbPath
) $LogPath

$ResearchReportStatus = Invoke-RCStep "ResearchReport" @(
    ".venv\Scripts\python.exe",
    "research_report.py"
) $LogPath

.venv\Scripts\python.exe v2_4_rc_validation.py `
    --import-status $ImportStatus `
    --generator-status $GeneratorStatus `
    --backtest-status $BacktestStatus `
    --strategy-comparison-status $StrategyComparisonStatus `
    --research-report-status $ResearchReportStatus `
    --qualification-json $QualificationJson `
    --log-path $LogPath `
    --output $ReportPath
