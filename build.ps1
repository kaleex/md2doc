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

    & $command @prefixArgs tools\md_to_pdf_cli.py partes dist\documento.pdf --title "Documento generado desde Markdown" --footer "Documento de trabajo"
    & $command @prefixArgs tools\md_to_docx_cli.py partes dist\documento.docx
}
finally {
    Pop-Location
}
