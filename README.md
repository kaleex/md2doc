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

Install from this repository on Windows:

```powershell
.\scripts\install.ps1
```

Install from this repository on Linux/macOS:

```bash
./scripts/install.sh
```

Both scripts install the `md2doc` command and, when `npm` is available, Mermaid
CLI for diagram rendering. To skip Mermaid:

```powershell
.\scripts\install.ps1 -SkipMermaid
```

```bash
./scripts/install.sh --skip-mermaid
```

Install optional external dependencies after `md2doc` is already installed:

```powershell
md2doc install-deps
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
    diagrams/
    context_diagram.png
  diagrams/
  dist/
```

Each document is independent: keep one folder per deliverable, proposal, report,
or architecture document.

Initialize the document folder as a Git repository:

```powershell
md2doc init my-document --git
```

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

`md2doc build` searches Markdown files inside `sections/` recursively by default,
so sections can be grouped in subfolders. Use numeric prefixes in folder and file
names to control ordering. To only process Markdown files directly inside
`sections/`, pass `--no-recursive`.

## Render Diagrams

Mermaid diagram sources live in `diagrams/`. They can be organized in
subfolders:

```text
my-document/
  diagrams/
    02_architecture/
      network.mmd
      identity.mmd
  assets/
    diagrams/
```

Render Mermaid diagrams to PNG assets:

```powershell
md2doc diagrams my-document
```

This writes images to `assets/diagrams/` while preserving the relative folder
layout:

```text
diagrams/02_architecture/network.mmd
assets/diagrams/02_architecture/network.png
```

Then reference the generated image from Markdown:

```markdown
![Network](../../assets/diagrams/02_architecture/network.png){width=16}
```

`md2doc diagrams` uses Mermaid CLI (`mmdc`) by default. Install it with:

```powershell
npm install -g @mermaid-js/mermaid-cli
```

Existing Python-based diagram tools are also supported. For projects that keep
diagram scripts under `tools/diagrams/` and generate images into `assets_temp/`,
run:

```powershell
md2doc diagrams my-document --renderer python --source tools/diagrams --output assets --pattern *.py
```

This executes each Python diagram script as a project module, then copies
generated images from `assets_temp/` to `assets/`. This is useful for tools based
on the Python `diagrams` package. That package is installed with `md2doc`; the
Graphviz system binary is still required by `diagrams`.

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

Because builds are deterministic, the included GitHub Actions workflow validates
the project on pull requests and branch pushes without relying on paid external
services:

- lint and tests
- Python package build
- sample PDF/DOCX build
- Bandit static security scan, failing on medium/high severity findings
- pip-audit dependency scan
- GitHub CodeQL analysis
- short-retention document artifacts
- GitOps dry-run that validates release metadata

The workflow runs on GitHub-hosted runners. Public repositories usually have
free hosted runner usage; private repositories may consume the account's
included minutes depending on the GitHub plan.

Branching follows a lightweight GitFlow model. See `docs/gitflow.md` for the
working rules for `main`, `develop`, `feature/**`, `release/**`, and `hotfix/**`.

A minimal build-only pipeline would look like this:

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
