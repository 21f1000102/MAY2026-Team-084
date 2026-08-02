<#
    SocietyEase — API test runner

    Runs the whole pytest suite and prints a readable, screenshot-friendly
    summary: environment, live test output, per-module results and a
    pass/fail box.

        cd Backend
        .\run_tests.ps1              # run everything
        .\run_tests.ps1 -Detailed    # show every individual test name
        .\run_tests.ps1 -Report      # also regenerate docs/TEST_CASES.md

    If PowerShell blocks the script, allow it for this session with:
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#>
[CmdletBinding()]
param(
    [switch]$Report,
    [switch]$Detailed
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Write-Rule([string]$Char = '=') { Write-Host ($Char * 74) -ForegroundColor DarkGray }

Write-Host ''
Write-Rule
Write-Host '   SocietyEase  --  Apartment Association Management System' -ForegroundColor Cyan
Write-Host '   REST API test suite' -ForegroundColor Cyan
Write-Rule
Write-Host ''

# ── environment ───────────────────────────────────────────────
Write-Host 'Environment' -ForegroundColor Yellow
try { $py = (python --version 2>&1 | Out-String).Trim() } catch { $py = 'not found' }
try { $pt = (python -m pytest --version 2>&1 | Select-Object -First 1 | Out-String).Trim() }
catch { $pt = 'not found' }
Write-Host ("  Python       : {0}" -f $py)
Write-Host ("  pytest       : {0}" -f $pt)
Write-Host ("  Working dir  : {0}" -f (Get-Location).Path)
Write-Host ("  Started      : {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Write-Host ''

if ($pt -like '*not found*' -or [string]::IsNullOrWhiteSpace($pt)) {
    Write-Host 'pytest is not installed. Run:  pip install -r requirements.txt' -ForegroundColor Red
    exit 1
}

# ── run the suite (once) ──────────────────────────────────────
Write-Host 'Running tests' -ForegroundColor Yellow
Write-Rule '-'

$xml = Join-Path $PSScriptRoot 'tests\_run.xml'
$startedAt = Get-Date

$pytestArgs = @('-m', 'pytest', '--color=yes', "--junit-xml=$xml")
if ($Detailed) { $pytestArgs += '-v' } else { $pytestArgs += @('-q', '--tb=short') }

# No assignment here: output streams to the console as it happens.
& python @pytestArgs 2>&1 | Tee-Object -Variable captured
$exitCode = $LASTEXITCODE
$elapsed = (Get-Date) - $startedAt

Write-Rule '-'
Write-Host ''

# ── per-module breakdown, parsed from the JUnit XML ───────────
$passed = 0; $failed = 0; $skipped = 0; $errors = 0; $total = 0

if (Test-Path $xml) {
    [xml]$doc = Get-Content $xml -Raw
    $suite = if ($doc.testsuites) { $doc.testsuites.testsuite } else { $doc.testsuite }

    $total   = [int]$suite.tests
    $failed  = [int]$suite.failures
    $errors  = [int]$suite.errors
    $skipped = [int]$suite.skipped
    $passed  = $total - $failed - $errors - $skipped

    $friendly = @{
        'test_auth' = 'Authentication'; 'test_members' = 'Members and Apartments'
        'test_complaints' = 'Complaints'; 'test_invoices' = 'Invoices and Payments'
        'test_expenses' = 'Expenses'; 'test_notices' = 'Notices'
        'test_polls' = 'Polls and Voting'; 'test_maintenance' = 'Maintenance Tasks'
        'test_equipment' = 'Equipment Predictor'; 'test_health' = 'Society Health Score'
        'test_conflicts' = 'Conflict Resolver'; 'test_parking' = 'Visitor Parking'
        'test_emergency' = 'Emergency Contacts'
        'test_regressions' = 'Regression suite (fixed defects)'
    }

    $stats = [ordered]@{}
    foreach ($tc in $suite.testcase) {
        $mod = ($tc.classname -split '\.' | Where-Object { $_ -and $_ -ne 'tests' } | Select-Object -First 1)
        if (-not $mod) { continue }
        if (-not $stats.Contains($mod)) { $stats[$mod] = @{ n = 0; bad = 0; skip = 0 } }
        $stats[$mod].n++
        if ($tc.failure -or $tc.error) { $stats[$mod].bad++ }
        elseif ($tc.skipped)           { $stats[$mod].skip++ }
    }

    Write-Host 'Results by module' -ForegroundColor Yellow
    Write-Host ''
    Write-Host ('  {0,-34} {1,6} {2,7}   {3}' -f 'MODULE', 'CASES', 'PASSED', 'STATUS') -ForegroundColor DarkGray
    Write-Host ('  {0}' -f ('-' * 66)) -ForegroundColor DarkGray

    foreach ($key in $stats.Keys) {
        $s = $stats[$key]
        $name = if ($friendly.ContainsKey($key)) { $friendly[$key] } else { $key }
        $ok = $s.n - $s.bad - $s.skip
        if ($s.bad -gt 0)       { $status = 'FAILED';     $colour = 'Red' }
        elseif ($s.skip -gt 0)  { $status = 'passed (1 skipped)'; $colour = 'Yellow' }
        else                    { $status = 'all passed'; $colour = 'Green' }
        Write-Host ('  {0,-34} {1,6} {2,7}   ' -f $name, $s.n, $ok) -NoNewline
        Write-Host $status -ForegroundColor $colour
    }

    Write-Host ('  {0}' -f ('-' * 66)) -ForegroundColor DarkGray
    Write-Host ('  {0,-34} {1,6} {2,7}' -f 'TOTAL', $total, $passed) -ForegroundColor Cyan
    Write-Host ''
    Remove-Item $xml -ErrorAction SilentlyContinue
}
else {
    # fall back to scraping the console summary line
    $plain = [regex]::Replace((($captured | Out-String)), "`e\[[0-9;]*m", '')
    if ($plain -match '(\d+)\s+passed')  { $passed  = [int]$Matches[1] }
    if ($plain -match '(\d+)\s+failed')  { $failed  = [int]$Matches[1] }
    if ($plain -match '(\d+)\s+skipped') { $skipped = [int]$Matches[1] }
    $total = $passed + $failed + $skipped
}

# ── summary box ───────────────────────────────────────────────
Write-Rule
if ($exitCode -eq 0) { Write-Host '   RESULT:  ALL TESTS PASSED' -ForegroundColor Green }
else                 { Write-Host '   RESULT:  TESTS FAILED'     -ForegroundColor Red }
Write-Rule
Write-Host ''
Write-Host ('   Total test cases : {0}' -f $total)
Write-Host ('   Passed           : {0}' -f $passed) -ForegroundColor Green
if ($failed -gt 0)  { Write-Host ('   Failed           : {0}' -f $failed) -ForegroundColor Red }
else                { Write-Host  '   Failed           : 0' }
if ($errors  -gt 0) { Write-Host ('   Errors           : {0}' -f $errors) -ForegroundColor Red }
if ($skipped -gt 0) { Write-Host ('   Skipped          : {0}  (documented open finding)' -f $skipped) -ForegroundColor Yellow }
Write-Host ('   Duration         : {0:N1}s' -f $elapsed.TotalSeconds)
Write-Host ('   Finished         : {0}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Write-Host ''
Write-Rule
Write-Host ''

if ($Report) {
    Write-Host 'Regenerating docs/TEST_CASES.md ...' -ForegroundColor Yellow
    & python tests/report.py
    Write-Host ''
}

Write-Host 'Full case-by-case detail (URL, request, expected vs actual):' -ForegroundColor DarkGray
Write-Host '  docs\TEST_CASES.md' -ForegroundColor DarkGray
Write-Host ''

exit $exitCode
