$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root
try {
    if (-not (Test-Path -LiteralPath "dist")) {
        New-Item -ItemType Directory -Path "dist" | Out-Null
    }

    $python = @("python")
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $python = @("uv", "run", "python")
    }
    $command = $python[0]
    $prefixArgs = @()
    if ($python.Length -gt 1) {
        $prefixArgs = $python[1..($python.Length - 1)]
    }

    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv run md2doc build . --title "Document generated from Markdown" --footer "Working document"
        return
    }

    & $command @prefixArgs -m md2doc.cli build . --title "Document generated from Markdown" --footer "Working document"
}
finally {
    Pop-Location
}
