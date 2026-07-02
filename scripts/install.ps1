param(
    [switch]$SkipMermaid
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location $Root
try {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv tool install --reinstall .
    }
    else {
        $Python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $Python) {
            throw "Python was not found. Install Python 3.11+ or uv first."
        }
        python -m pip install --user .
    }

    if (-not $SkipMermaid) {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            npm install -g @mermaid-js/mermaid-cli
        }
        else {
            Write-Warning "npm was not found. Install Node.js/npm, then run: md2doc install-deps"
        }
    }

    md2doc --help | Out-Null
    Write-Host "md2doc installed successfully."
}
finally {
    Pop-Location
}
