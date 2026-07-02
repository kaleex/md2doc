# md2doc

Create PDF and DOCX documents from Markdown project templates.

This repository is packaged for PyPI as `kaleex-md2doc` and exposes the `md2doc`
command.

## Install

From PyPI, once published:

```powershell
pip install kaleex-md2doc
```

For isolated CLI usage:

```powershell
pipx install kaleex-md2doc
```

During local development:

```powershell
uv sync
uv run md2doc --help
```

## Create A Document Project

```powershell
md2doc init my-document
```

This creates:

```text
my-document/
  sections/
    00_cover.md
    01_content.md
  assets/
    context_diagram.png
  diagrams/
  dist/
```

Each document is independent: keep one folder per deliverable, proposal, report,
or architecture document.

## Build Outputs

From inside a document folder:

```powershell
md2doc build
```

From outside:

```powershell
md2doc build my-document
```

This generates:

```text
dist/document.pdf
dist/document.docx
```

Generate only one format:

```powershell
md2doc build my-document --format pdf
md2doc build my-document --format docx
```

Customize output metadata:

```powershell
md2doc build my-document --name architecture --title "Architecture v0" --footer "Working document"
```

## Local Template Example

This repository also contains a sample document in `sections/` and `assets/`.
You can build it with:

```powershell
uv run md2doc build
```

Or, on Windows:

```powershell
.\build.ps1
```

## Add Figures

Store images in `assets/` and reference them from Markdown files:

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

## Template-Oriented Workflow

The package currently ships one template: `default`.

```powershell
md2doc init customer-report --template default
md2doc build customer-report --name customer-report
```

The intended scaling model is one folder per document and templates that scaffold
the folder structure, example sections, assets, and build defaults.
