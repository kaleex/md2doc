from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLUE = colors.HexColor("#1F4E79")
LIGHT_BLUE = colors.HexColor("#EAF3FA")
GRID = colors.HexColor("#333333")
MUTED = colors.HexColor("#666666")

STRUCTURE_HELP = """\
Recommended structure:

  my_document/
    sections/
      00_cover.md
      01_summary.md
      02_architecture/
        00_context.md
        01_decisions.md
    diagrams/
      02_architecture/
        network.mmd
    assets/
      02_architecture/
        network.png
      context_diagram.png
      data_flow.png
    dist/
      document.pdf
      document.docx

Recommended usage:

  md2doc build my_document --format pdf

Generate all outputs:

  md2doc build my_document

Render Mermaid diagrams:

  md2doc diagrams my_document

Render Python diagram scripts:

  md2doc diagrams my_document --renderer python --source tools/diagrams
    --output assets --pattern *.py

Figures:

  Store images in assets/ and reference them from each Markdown file:

  ![Figure 1. Context diagram](../assets/context_diagram.png){width=16}

Supported Markdown:

  # Heading 1
  ## Heading 2
  ### Heading 3

  Normal paragraphs separated by blank lines.

  - Simple list item
  - Another item

  | Column A | Column B |
  | --- | --- |
  | Value | Value |

  > [!NOTE] Note title
  > Note body.

  {{pagebreak}}

Notes:

  - md2doc build searches section subfolders by default.
  - If you pass a folder, .md files are processed alphabetically by path.
  - Use numeric prefixes in folders and files to control order: 00_, 01_, 02_...
  - Image paths are resolved from the Markdown file where they appear.
  - Image width is expressed in centimeters and capped at the usable page width.
"""


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}
    styles["body"] = ParagraphStyle(
        "MarkdownBody",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=9.4,
        leading=11.4,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    styles["h1"] = ParagraphStyle(
        "MarkdownH1",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=BLUE,
        spaceBefore=13,
        spaceAfter=8,
        keepWithNext=True,
    )
    styles["h2"] = ParagraphStyle(
        "MarkdownH2",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        textColor=BLUE,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    styles["h3"] = ParagraphStyle(
        "MarkdownH3",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        fontSize=10.8,
        leading=13,
        textColor=BLUE,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    styles["caption"] = ParagraphStyle(
        "MarkdownCaption",
        parent=styles["body"],
        fontSize=8,
        leading=10,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceBefore=3,
        spaceAfter=8,
    )
    styles["table"] = ParagraphStyle(
        "MarkdownTable",
        parent=styles["body"],
        fontSize=7.9,
        leading=9.5,
        spaceAfter=0,
    )
    styles["table_header"] = ParagraphStyle(
        "MarkdownTableHeader",
        parent=styles["table"],
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    styles["callout_title"] = ParagraphStyle(
        "MarkdownCalloutTitle",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        fontSize=9.2,
        leading=11,
        spaceAfter=3,
    )
    return styles


STYLES = make_styles()


def clean_inline(text: str) -> str:
    safe = html.escape(text.strip())
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"\*(.+?)\*", r"<i>\1</i>", safe)
    safe = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", safe)
    safe = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", safe)
    return safe.replace("&lt;br&gt;", "<br/>")


def para(text: str, style: str = "body") -> Paragraph:
    return Paragraph(clean_inline(text), STYLES[style])


def parse_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    separator = r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?"
    for line in lines:
        stripped = line.strip()
        if re.fullmatch(separator, stripped):
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    max_cols = max((len(row) for row in rows), default=0)
    return [row + [""] * (max_cols - len(row)) for row in rows]


def table_flowable(table_lines: list[str], available_width: float):
    rows = parse_table(table_lines)
    if not rows:
        return Spacer(1, 1)

    data = []
    for r_idx, row in enumerate(rows):
        style_name = "table_header" if r_idx == 0 else "table"
        data.append([Paragraph(clean_inline(cell), STYLES[style_name]) for cell in row])

    max_cols = len(rows[0])
    col_width = available_width / max_cols
    table = Table(data, colWidths=[col_width] * max_cols, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def parse_image(line: str, md_path: Path):
    match = re.match(r"!\[(.*?)\]\((.*?)\)(?:\{width=([0-9.]+)\})?", line.strip())
    if not match:
        return None

    caption, raw_path, raw_width = match.groups()
    img_path = (md_path.parent / raw_path).resolve()
    width_cm = float(raw_width) if raw_width else 16.0
    return img_path, caption, width_cm * cm


def image_flowable(img_path: Path, caption: str, width: float, available_width: float):
    if not img_path.exists():
        return para(f"[Image not found: {img_path}]")

    width = min(width, available_width)
    with PILImage.open(img_path) as src:
        img_w, img_h = src.size
    height = width * (img_h / img_w)
    return KeepTogether(
        [Image(str(img_path), width=width, height=height), para(caption, "caption")]
    )


def callout_flowable(title: str, body: str, available_width: float):
    content = [
        Paragraph(clean_inline(title), STYLES["callout_title"]),
        Paragraph(clean_inline(body), STYLES["body"]),
    ]
    table = Table([[content]], colWidths=[available_width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.6, GRID),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def md_to_flowables(md_path: Path, available_width: float):
    lines = md_path.read_text(encoding="utf-8-sig").splitlines()
    flow = []
    paragraph: list[str] = []
    table_lines: list[str] = []
    bullets: list[str] = []
    callout_title: str | None = None
    callout_body: list[str] = []
    in_comment = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            flow.append(para(" ".join(paragraph)))
            paragraph = []

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            flow.append(table_flowable(table_lines, available_width))
            flow.append(Spacer(1, 8))
            table_lines = []

    def flush_bullets() -> None:
        nonlocal bullets
        if bullets:
            items = [ListItem(para(item), leftIndent=12) for item in bullets]
            flow.append(ListFlowable(items, bulletType="bullet", leftIndent=18))
            flow.append(Spacer(1, 4))
            bullets = []

    def flush_callout() -> None:
        nonlocal callout_title, callout_body
        if callout_title:
            flow.append(callout_flowable(callout_title, " ".join(callout_body), available_width))
            flow.append(Spacer(1, 8))
            callout_title = None
            callout_body = []

    for raw in lines:
        line = raw.rstrip().lstrip("\ufeff")
        stripped = line.strip()

        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            in_comment = "-->" not in line
            continue
        if stripped == "{{pagebreak}}":
            flush_paragraph()
            flush_table()
            flush_bullets()
            flush_callout()
            flow.append(PageBreak())
            continue
        if not stripped:
            flush_paragraph()
            flush_table()
            flush_bullets()
            flush_callout()
            continue
        if line.startswith("> [!NOTE]"):
            flush_paragraph()
            flush_table()
            flush_bullets()
            flush_callout()
            callout_title = line.replace("> [!NOTE]", "", 1).strip() or "Note"
            callout_body = []
            continue
        if callout_title and line.startswith(">"):
            callout_body.append(line[1:].strip())
            continue
        if line.startswith("|"):
            flush_paragraph()
            flush_bullets()
            flush_callout()
            table_lines.append(line)
            continue

        image = parse_image(line, md_path)
        if image:
            flush_paragraph()
            flush_table()
            flush_bullets()
            flush_callout()
            img_path, caption, width = image
            flow.append(image_flowable(img_path, caption, width, available_width))
            continue
        if line.startswith("- "):
            flush_paragraph()
            flush_table()
            flush_callout()
            bullets.append(line[2:].strip())
            continue
        if line.startswith("#"):
            flush_paragraph()
            flush_table()
            flush_bullets()
            flush_callout()
            level = min(len(line) - len(line.lstrip("#")), 3)
            text = line[level:].strip()
            flow.append(Paragraph(clean_inline(text), STYLES[f"h{level}"]))
            continue

        paragraph.append(stripped)

    flush_paragraph()
    flush_table()
    flush_bullets()
    flush_callout()
    return flow


def collect_markdown_files(input_path: Path, pattern: str, recursive: bool) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    files = input_path.rglob(pattern) if recursive else input_path.glob(pattern)
    return sorted(path for path in files if path.is_file())


def build_pdf(
    input_path: Path,
    output_path: Path,
    pattern: str,
    recursive: bool,
    title: str,
    footer: str,
    author: str,
) -> Path:
    md_files = collect_markdown_files(input_path, pattern, recursive)
    if not md_files:
        raise FileNotFoundError(
            f"No Markdown files matching pattern {pattern!r} were found in {input_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.45 * cm,
        leftMargin=1.45 * cm,
        topMargin=1.55 * cm,
        bottomMargin=1.35 * cm,
        title=title,
        author=author,
    )
    available_width = A4[0] - doc.leftMargin - doc.rightMargin
    story = []
    for index, md_path in enumerate(md_files):
        if index > 0:
            story.append(PageBreak())
        story.extend(md_to_flowables(md_path, available_width))

    def page_canvas(canvas, built_doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(built_doc.leftMargin, A4[1] - 1.0 * cm, title)
        canvas.drawString(built_doc.leftMargin, 0.8 * cm, footer)
        canvas.drawRightString(A4[0] - built_doc.rightMargin, 0.8 * cm, str(canvas.getPageNumber()))
        canvas.restoreState()

    doc.build(story, onFirstPage=page_canvas, onLaterPages=page_canvas)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one or more Markdown files to PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=STRUCTURE_HELP,
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="A .md file or a folder with .md files. Folders are processed by filename.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="Output PDF path. Example: dist/document.pdf.",
    )
    parser.add_argument(
        "--pattern",
        default="*.md",
        help="Markdown file pattern when input is a folder. Default: *.md",
    )
    parser.add_argument("--recursive", action="store_true", help="Search Markdown in subfolders.")
    parser.add_argument(
        "--title",
        default="Document generated from Markdown",
        help="PDF title.",
    )
    parser.add_argument("--footer", default="Working document", help="Page footer text.")
    parser.add_argument("--author", default="", help="Author in PDF metadata.")
    parser.add_argument(
        "--print-structure",
        action="store_true",
        help="Print the recommended structure and exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.print_structure:
        print(STRUCTURE_HELP)
        return

    if not args.input or not args.output:
        raise SystemExit("Usage: md2doc build <document-folder> --format pdf")

    output_path = build_pdf(
        args.input,
        args.output,
        args.pattern,
        args.recursive,
        args.title,
        args.footer,
        args.author,
    )
    print(output_path)


if __name__ == "__main__":
    main()
