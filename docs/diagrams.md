# Diagram Workflow

`md2doc` separates diagram sources from rendered images:

- `diagrams/`: diagram-as-code sources, such as Mermaid `.mmd` files.
- `tools/diagrams/`: optional Python diagram generators.
- `assets/`: rendered images referenced by Markdown sections.

Markdown and DOCX/PDF builders only read images from `assets/`. Diagram
rendering is a separate step.

## Mermaid

Store Mermaid sources under `diagrams/`:

```text
my-document/
  diagrams/
    02_architecture/
      network.mmd
  assets/
```

Render them:

```powershell
md2doc diagrams my-document
```

This preserves relative paths under `assets/`:

```text
diagrams/02_architecture/network.mmd
assets/02_architecture/network.png
```

Reference the generated image from a Markdown file:

```markdown
![Network](../../assets/02_architecture/network.png){width=16}
```

The Mermaid renderer uses `mmdc`, provided by Mermaid CLI:

```powershell
npm install -g @mermaid-js/mermaid-cli
```

## Python Generators

Some projects generate diagrams with Python scripts instead of Mermaid. Keep
those scripts under `tools/diagrams/`:

```text
my-document/
  tools/
    diagrams/
      __init__.py
      network.py
  assets/
```

Run:

```powershell
uv run --with diagrams md2doc diagrams my-document --renderer python --source tools/diagrams --output assets --pattern *.py
```

The Python renderer executes each script as a module. It exposes these
environment variables:

- `MD2DOC_PROJECT_ROOT`: document project root.
- `MD2DOC_ASSETS_DIR`: target assets folder.
- `MD2DOC_OUTPUT_DIR`: target output folder for generated diagrams.

Generator code should write images directly to `MD2DOC_OUTPUT_DIR`.

Example:

```python
from pathlib import Path
import os

OUTPUT_DIR = Path(os.environ.get("MD2DOC_OUTPUT_DIR", "assets"))
OUT = OUTPUT_DIR / "network.png"
```

The Python renderer uses the same Python interpreter that runs `md2doc`. Use
`uv run --with ...` for one-off dependencies, or pass `--executable` if a
document project has its own virtual environment:

```powershell
md2doc diagrams my-document --renderer python --source tools/diagrams --output assets --pattern *.py --executable .venv\Scripts\python.exe
```

The Python `diagrams` package also requires the Graphviz system binary.
