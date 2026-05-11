# smoke_prod.ps1 — Production smoke test for India H2 Workforce Atlas
# Runs Sun May 17 morning per plan line 87. Do NOT run before URL freeze.
#
# Usage:
#   .\scripts\smoke_prod.ps1
#   .\scripts\smoke_prod.ps1 -BaseUrl "https://e740554.github.io/india-h2-jobs"
#
# Exits with non-zero on any failure.

param(
    [string]$BaseUrl = "https://hygoat.in/workforce-atlas"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$FreezeFile = Join-Path $RepoRoot "URL_FREEZE.md"

$failures = 0

function Assert-Http200 {
    param([string]$Url, [string]$Label)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
        if ($response.StatusCode -eq 200) {
            Write-Host "[PASS] $Label — HTTP 200" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $Label — HTTP $($response.StatusCode)" -ForegroundColor Red
            $global:failures++
        }
    } catch {
        Write-Host "[FAIL] $Label — $($_.Exception.Message)" -ForegroundColor Red
        $global:failures++
    }
}

function Assert-Content {
    param([string]$Url, [string]$Label, [string[]]$MustContain)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
        if ($response.StatusCode -ne 200) {
            Write-Host "[FAIL] $Label — HTTP $($response.StatusCode) (expected 200)" -ForegroundColor Red
            $global:failures++
            return
        }
        $body = $response.Content
        $allFound = $true
        foreach ($needle in $MustContain) {
            if ($body -notmatch [regex]::Escape($needle)) {
                Write-Host "[FAIL] $Label — missing: '$needle'" -ForegroundColor Red
                $allFound = $false
            }
        }
        if ($allFound) {
            Write-Host "[PASS] $Label — all content markers found" -ForegroundColor Green
        } else {
            $global:failures++
        }
    } catch {
        Write-Host "[FAIL] $Label — $($_.Exception.Message)" -ForegroundColor Red
        $global:failures++
    }
}

Write-Host "=== Smoke test: $BaseUrl ===" -ForegroundColor Cyan

# 1. HTTP 200 on every URL_FREEZE.md path
Write-Host ""
Write-Host "--- 1. URL freeze path validation ---"
$urls = @(
    "$BaseUrl",
    "$BaseUrl/methodology/",
    "$BaseUrl/about/",
    "$BaseUrl/?lens=maritime"
)
foreach ($u in $urls) {
    Assert-Http200 -Url $u -Label $u
}

# 2. Atlas root content markers
Write-Host ""
Write-Host "--- 2. Atlas root content ---"
Assert-Content -Url "$BaseUrl" -Label "Atlas root" -MustContain @(
    "Loading 1,802 occupations",
    "India H2 Workforce Atlas"
)

# 3. Methodology page content markers
Write-Host ""
Write-Host "--- 3. Methodology page ---"
Assert-Content -Url "$BaseUrl/methodology/" -Label "Methodology" -MustContain @(
    "Mukta",
    "../style.css",
    "PLFS 2023-24",
    "scored against the H"
)

# 4. About page content markers
Write-Host ""
Write-Host "--- 4. About page ---"
Assert-Content -Url "$BaseUrl/about/" -Label "About" -MustContain @(
    "Contact",
    "ekansh@ekavikalp.com",
    "../style.css"
)

# 5. Maritime lens page delivers content
Write-Host ""
Write-Host "--- 5. Lens parameter validation ---"
Assert-Content -Url "$BaseUrl/?lens=maritime" -Label "lens=maritime" -MustContain @(
    "India H2 Workforce Atlas"
)

Write-Host ""
if ($failures -eq 0) {
    Write-Host "=== ALL CHECKS PASSED ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== $failures FAILURE(S) DETECTED ===" -ForegroundColor Red
    exit 1
}
