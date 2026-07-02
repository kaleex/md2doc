# md2doc

Create PDF and DOCX documents from Markdown project templates.

This repository is packaged for PyPI as `kaleex-md2doc` and exposes the `md2doc`
command.

## Why

`md2doc` treats documentation as code. The source of truth is a versioned folder
with Markdown sections, assets, and generated outputs that can be rebuilt at any
time.

This makes document work fit naturally into DevOps and GitOps workflows:

- Reviews happen through pull requests instead of opaque binary edits.
- Document changes can be diffed, reviewed, approved, and reverted.
- CI jobs can rebuild PDF/DOCX artifacts from the same committed sources.
- Generated deliverables are reproducible across machines and environments.
- Templates keep document structure consistent across teams and projects.
- Each deliverable can live as an independent folder with its own sections,
  assets, diagrams, and outputs.

The goal is not to replace rich document editors for final polishing. The goal is
to make repeatable technical documentation, architecture packs, reports, and
delivery documents easier to govern with the same habits used for software.

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

## CI/CD Example

Because builds are deterministic, a pipeline can generate deliverables on every
merge:

```yaml
name: docs

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run md2doc build examples/customer-report --name customer-report
```

In a GitOps setup, the repository remains the desired state for the document:
Markdown and assets are reviewed first, generated artifacts are produced by the
pipeline, and releases can attach the resulting PDF/DOCX files.
