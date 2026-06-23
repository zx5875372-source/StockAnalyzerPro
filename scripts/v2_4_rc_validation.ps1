Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$DbPath = "v2_4_rc_test.db"
$FinancialCsv = "tests/sample_data/historical/financial_snapshots_valid.csv"
$ReportPath = "reports/v2_4_rc_validation.md"
$QualificationJson = "reports/backtest_qualification.json"

function Invoke-RCStep {
    param(
        [string]$Name,
        [string[]]$Command
    )

    Write-Host "[$Name] $($Command -join ' ')"
    & $Command[0] @($Command[1..($Command.Length - 1)])
    if ($LASTEXITCODE -eq 0) {
        return "pass"
    }
    return "fail(exit_code=$LASTEXITCODE)"
}

if (Test-Path -LiteralPath $DbPath) {
    Remove-Item -LiteralPath $DbPath
}

$ImportStatus = Invoke-RCStep "Import" @(
    ".venv\Scripts\python.exe",
    "historical_import.py",
    "--type",
    "financial",
    "--file",
    $FinancialCsv,
    "--db",
    $DbPath
)

$GeneratorStatus = Invoke-RCStep "Generator" @(
    ".venv\Scripts\python.exe",
    "historical_generate_sap.py",
    "--db",
    $DbPath
)

$BacktestStatus = Invoke-RCStep "Backtest" @(
    ".venv\Scripts\python.exe",
    "backtest.py",
    "--snapshot-source",
    "repository",
    "--snapshot-db",
    $DbPath
)

$StrategyComparisonStatus = Invoke-RCStep "StrategyComparison" @(
    ".venv\Scripts\python.exe",
    "strategy_compare.py",
    "--snapshot-source",
    "repository",
    "--snapshot-db",
    $DbPath
)

$ResearchReportStatus = Invoke-RCStep "ResearchReport" @(
    ".venv\Scripts\python.exe",
    "research_report.py"
)

.venv\Scripts\python.exe v2_4_rc_validation.py `
    --import-status $ImportStatus `
    --generator-status $GeneratorStatus `
    --backtest-status $BacktestStatus `
    --strategy-comparison-status $StrategyComparisonStatus `
    --research-report-status $ResearchReportStatus `
    --qualification-json $QualificationJson `
    --output $ReportPath
