# Markdown to DOCX/PDF Template

A clean, reproducible template for generating Word `.docx` and PDF documents from Markdown.

## Installation

With `uv`:

```powershell
uv sync
```

If you have `make` available:

```powershell
make install
```

## Recommended Structure

```text
my_document/
  sections/
    00_cover.md
    01_summary.md
    02_architecture.md
  assets/
    context_diagram.png
    data_flow.png
  dist/
    document.docx
    document.pdf
  tools/
    md_to_docx_cli.py
    md_to_pdf_cli.py
  Makefile
  build.ps1
  requirements.txt
  pyproject.toml
```

Use numeric prefixes in `sections/` to control the output order.

## Generate Everything

```powershell
make build
```

On Windows, if you do not have `make`, use:

```powershell
.\build.ps1
```

This generates:

```text
dist/document.pdf
dist/document.docx
```

You can customize the output name, title, and footer:

```powershell
make build DOC_NAME=architecture DOC_TITLE="Architecture v0" DOC_FOOTER="Working document"
```

## Generate Separately

```powershell
make pdf
make docx
```

Without `make`:

```powershell
python tools\md_to_docx_cli.py sections dist\document.docx
python tools\md_to_pdf_cli.py sections dist\document.pdf --title "My document" --footer "Working document"
```

Without `make`, but using `uv`:

```powershell
uv run python tools\md_to_docx_cli.py sections dist\document.docx
uv run python tools\md_to_pdf_cli.py sections dist\document.pdf --title "My document" --footer "Working document"
```

## Add Figures

Store images in `assets/` and reference them from the Markdown files:

```markdown
![Figure 1. Context diagram](../assets/context_diagram.png){width=16}
```

`width` is expressed in centimeters. If omitted, the default is `16`.

## Supported Markdown

```markdown
# Heading 1
## Heading 2
### Heading 3

A normal paragraph separated by blank lines.

- Simple list item
- Another item

| Column A | Column B |
| --- | --- |
| Value | Value |

> [!NOTE] Note
> Note body.

{{pagebreak}}
```

## Built-In Help

```powershell
python tools\md_to_docx_cli.py --help
python tools\md_to_pdf_cli.py --help
python tools\md_to_pdf_cli.py --print-structure
make structure
```
