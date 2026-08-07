<#
.SYNOPSIS
    Build the lc-agent frontend only (do not restart the Python server).

.DESCRIPTION
    Runs `npm run build` in D:\codes\lc-agent\frontend.
    Use this when only frontend files (.vue / .ts / .css / etc.) have changed.
#>

$ErrorActionPreference = 'Stop'

$frontendDir = 'D:\codes\lc-agent\frontend'

Write-Host "[build-frontend] Building frontend in $frontendDir ..." -ForegroundColor Cyan

Push-Location $frontendDir
try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "npm run build failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host "[build-frontend] Build finished. Output: D:\codes\lc-agent\lc_agent\web\dist\" -ForegroundColor Green
