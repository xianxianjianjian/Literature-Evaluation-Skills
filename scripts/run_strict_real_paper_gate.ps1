param(
    [Parameter(Mandatory = $true)]
    [string]$WorkDir,

    [Parameter(Mandatory = $true)]
    [string]$ReferencePdf,

    [Parameter(Mandatory = $true)]
    [string]$OutputPdf,

    [string]$Python = "python",

    [string]$ReviewedLedger = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkDir = [System.IO.Path]::GetFullPath($WorkDir)
$ReferencePdf = [System.IO.Path]::GetFullPath($ReferencePdf)
$OutputPdf = [System.IO.Path]::GetFullPath($OutputPdf)
$FontPath = "C:\Windows\Fonts\simsun.ttc"
$LedgerPath = Join-Path $WorkDir "translation_ledger.jsonl"
$FontMapPath = Join-Path $WorkDir "font_map.json"
$PlanPath = Join-Path $WorkDir "mirror_layout_plan.json"
$ReportPath = Join-Path $WorkDir "strict_real_paper_validation.json"
$RecoveryReportPath = Join-Path $WorkDir "overlay_recovery_report.json"
$RecoveryTasksPath = Join-Path $WorkDir "translation_recovery_tasks.jsonl"
$PartialLedgerPath = Join-Path $WorkDir "translation_ledger.partial.jsonl"

# Windows PowerShell 5.1 does not define the PowerShell 6+ automatic
# variable $IsWindows. Use the process OS marker instead so the production
# gate works in both Windows PowerShell 5.1 and PowerShell 7+.
$RunningOnWindows = ($env:OS -eq "Windows_NT")
if (-not $RunningOnWindows) {
    throw "The strict production gate must run on Windows with the installed SimSun font."
}
if (-not (Test-Path -LiteralPath $WorkDir -PathType Container)) {
    throw "WorkDir does not exist: $WorkDir"
}
if (-not (Test-Path -LiteralPath $ReferencePdf -PathType Leaf)) {
    throw "Reference translated mirror PDF does not exist: $ReferencePdf"
}
if (-not (Test-Path -LiteralPath $FontPath -PathType Leaf)) {
    throw "Production SimSun is missing: $FontPath"
}

Write-Host "[1/7] Validate the installed production SimSun runtime"
& $Python (Join-Path $ScriptDir "validate_simsun_runtime.py")
if ($LASTEXITCODE -ne 0) { throw "SimSun runtime validation failed." }

if ($ReviewedLedger -ne "") {
    $ReviewedLedger = [System.IO.Path]::GetFullPath($ReviewedLedger)
    if (-not (Test-Path -LiteralPath $ReviewedLedger -PathType Leaf)) {
        throw "Reviewed ledger does not exist: $ReviewedLedger"
    }
    Write-Host "[2/7] Use the explicitly reviewed frame-linked translation ledger"
    Copy-Item -LiteralPath $ReviewedLedger -Destination $LedgerPath -Force
    Write-Host "Reviewed ledger copied to: $LedgerPath"
} else {
    Write-Host "[2/7] Recover the complete frame-linked translation ledger from the prior reviewed mirror"
    & $Python (Join-Path $ScriptDir "recover_overlay_translation.py") `
        --work-dir $WorkDir `
        --reference-pdf $ReferencePdf `
        --output $LedgerPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Strict recovery stopped before rendering." -ForegroundColor Yellow
        if (Test-Path -LiteralPath $RecoveryReportPath) {
            Write-Host "Recovery report: $RecoveryReportPath" -ForegroundColor Yellow
        }
        if (Test-Path -LiteralPath $RecoveryTasksPath) {
            Write-Host "Translation review tasks: $RecoveryTasksPath" -ForegroundColor Yellow
        }
        if (Test-Path -LiteralPath $PartialLedgerPath) {
            Write-Host "Partial exact matches: $PartialLedgerPath" -ForegroundColor Yellow
        }
        throw "Overlay translation recovery requires reviewed legacy-mirror migration; exact rendering was not attempted."
    }
}

Write-Host "[3/7] Freeze the production SimSun font map"
& $Python (Join-Path $ScriptDir "mirror_pdf.py") create-font-map `
    --font-path $FontPath `
    --output $FontMapPath `
    --force
if ($LASTEXITCODE -ne 0) { throw "Font-map creation failed." }

Write-Host "[4/7] Rebuild the exact one-to-one layout plan against the requested output"
& $Python (Join-Path $ScriptDir "mirror_pdf.py") create-plan `
    --source-inventory (Join-Path $WorkDir "source_inventory.json") `
    --text-frame-inventory (Join-Path $WorkDir "text_frame_inventory.jsonl") `
    --font-map $FontMapPath `
    --plan-output $PlanPath `
    --output-pdf $OutputPdf `
    --layout-fidelity EXACT_TEXT_FRAME `
    --cjk-font-family SimSun `
    --minimum-font-scale 0.95 `
    --force
if ($LASTEXITCODE -ne 0) { throw "Exact layout-plan creation failed." }

Write-Host "[5/7] Render the full Main+SI PDF with the current PR exact renderer"
& $Python (Join-Path $ScriptDir "render_exact_mirror.py") `
    --work-dir $WorkDir `
    --output $OutputPdf
if ($LASTEXITCODE -ne 0) { throw "Exact rendering failed." }

Write-Host "[6/7] Independently validate page geometry, SimSun, frame containment, 95%-100% sizing and outside-frame pixels"
& $Python (Join-Path $ScriptDir "validate_translation_package.py") `
    --work-dir $WorkDir `
    --a-path $OutputPdf `
    --scope FULL_MIRROR `
    --layout-fidelity EXACT_TEXT_FRAME `
    --report $ReportPath
if ($LASTEXITCODE -ne 0) { throw "Independent exact-mirror validation failed." }

Write-Host "[7/7] Confirm the written report says passed=true"
$Report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json
if ($Report.passed -ne $true) {
    throw "Strict real-paper validation report did not pass."
}

Write-Host "STRICT REAL-PAPER GATE: PASS"
Write-Host "Output: $OutputPdf"
Write-Host "Report: $ReportPath"
