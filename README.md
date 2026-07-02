# Plantilla Markdown a DOCX/PDF

Plantilla limpia y reproducible para generar documentos Word `.docx` y PDF desde Markdown.

## Instalacion

Con `uv`:

```powershell
uv sync
```

Si tienes `make` disponible:

```powershell
make install
```

## Estructura recomendada

```text
mi_documento/
  partes/
    00_portada.md
    01_resumen.md
    02_arquitectura.md
  assets/
    diagrama_contexto.png
    flujo_datos.png
  dist/
    documento.docx
    documento.pdf
  tools/
    md_to_docx_cli.py
    md_to_pdf_cli.py
  Makefile
  build.ps1
  requirements.txt
  pyproject.toml
```

Usa prefijos numericos en `partes/` para controlar el orden de salida.

## Generar todo

```powershell
make build
```

En Windows, si no tienes `make`, puedes usar:

```powershell
.\build.ps1
```

Genera:

```text
dist/documento.pdf
dist/documento.docx
```

Puedes personalizar nombre, titulo y pie:

```powershell
make build DOC_NAME=arquitectura DOC_TITLE="Arquitectura v0" DOC_FOOTER="Documento de trabajo"
```

## Generar por separado

```powershell
make pdf
make docx
```

Sin `make`:

```powershell
python tools\md_to_docx_cli.py partes dist\documento.docx
python tools\md_to_pdf_cli.py partes dist\documento.pdf --title "Mi documento" --footer "Documento de trabajo"
```

Sin `make`, pero usando `uv`:

```powershell
uv run python tools\md_to_docx_cli.py partes dist\documento.docx
uv run python tools\md_to_pdf_cli.py partes dist\documento.pdf --title "Mi documento" --footer "Documento de trabajo"
```

## Meter figuras

Guarda las imagenes en `assets/` y referencialas desde los Markdown:

```markdown
![Figura 1. Diagrama de contexto](../assets/diagrama_contexto.png){width=16}
```

El `width` esta en centimetros. Si no lo pones, usa `16`.

## Markdown soportado

```markdown
# Titulo 1
## Titulo 2
### Titulo 3

Parrafo normal separado por lineas en blanco.

- Lista simple
- Otro punto

| Columna A | Columna B |
| --- | --- |
| Valor | Valor |

> [!NOTE] Nota
> Texto de la nota.

{{pagebreak}}
```

## Ayuda integrada

```powershell
python tools\md_to_docx_cli.py --help
python tools\md_to_pdf_cli.py --help
python tools\md_to_pdf_cli.py --print-structure
make structure
```
