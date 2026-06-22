Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

.venv\Scripts\python.exe finmind_import.py --symbol 2330 --start 2024-01-01 --end 2024-12-31 --db historical_snapshots_test.db
