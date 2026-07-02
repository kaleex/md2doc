from __future__ import annotations

import argparse
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from md2doc.docx_builder import build_docx
from md2doc.pdf_builder import build_pdf

DEFAULT_TITLE = "Document generated from Markdown"
DEFAULT_FOOTER = "Working document"


def copy_resource_tree(source: Traversable, target: Path, force: bool) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            copy_resource_tree(item, destination, force)
            continue

        if destination.exists() and not force:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(item.read_bytes())


def copy_template(target: Path, template: str, force: bool) -> Path:
    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(
            f"{target} already exists and is not empty. Use --force to copy into it."
        )

    template_root = resources.files("md2doc").joinpath("templates", template)
    if not template_root.is_dir():
        raise FileNotFoundError(f"Unknown template: {template}")

    target.mkdir(parents=True, exist_ok=True)
    copy_resource_tree(template_root, target, force)
    for folder in ("assets", "diagrams", "dist", "sections"):
        (target / folder).mkdir(parents=True, exist_ok=True)
    return target


def build_document(
    root: Path,
    output_format: str,
    output_name: str,
    title: str,
    footer: str,
    author: str,
    sections: str,
    dist: str,
) -> list[Path]:
    source = root / sections
    output_dir = root / dist
    outputs: list[Path] = []

    if output_format in {"pdf", "all"}:
        outputs.append(
            build_pdf(
                source,
                output_dir / f"{output_name}.pdf",
                "*.md",
                False,
                title,
                footer,
                author,
            )
        )

    if output_format in {"docx", "all"}:
        outputs.append(build_docx(source, output_dir / f"{output_name}.docx", "*.md", False))

    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="md2doc",
        description="Create and build Markdown-based PDF/DOCX document projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new document project.")
    init_parser.add_argument("target", type=Path, help="Target folder for the document project.")
    init_parser.add_argument(
        "--template",
        default="default",
        help="Template name. Default: default",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow copying into an existing non-empty folder.",
    )

    build_parser = subparsers.add_parser("build", help="Build PDF and/or DOCX outputs.")
    build_parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Document project root. Default: current directory.",
    )
    build_parser.add_argument(
        "--format",
        choices=["all", "pdf", "docx"],
        default="all",
        help="Output format to generate. Default: all",
    )
    build_parser.add_argument(
        "--name",
        default="document",
        help="Output filename without extension.",
    )
    build_parser.add_argument("--title", default=DEFAULT_TITLE, help="PDF title/header text.")
    build_parser.add_argument("--footer", default=DEFAULT_FOOTER, help="PDF footer text.")
    build_parser.add_argument("--author", default="", help="PDF author metadata.")
    build_parser.add_argument("--sections", default="sections", help="Sections folder name.")
    build_parser.add_argument("--dist", default="dist", help="Output folder name.")

    subparsers.add_parser("structure", help="Print the recommended Markdown structure.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "init":
        target = copy_template(args.target, args.template, args.force)
        print(target)
        return

    if args.command == "build":
        outputs = build_document(
            args.root,
            args.format,
            args.name,
            args.title,
            args.footer,
            args.author,
            args.sections,
            args.dist,
        )
        for output in outputs:
            print(output)
        return

    if args.command == "structure":
        from md2doc.pdf_builder import STRUCTURE_HELP

        print(STRUCTURE_HELP)


if __name__ == "__main__":
    main()
