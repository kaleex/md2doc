from __future__ import annotations

import argparse
import subprocess
import sys
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from md2doc.diagrams import render_mermaid_diagrams, render_python_diagrams
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
    try:
        target_exists = target.exists()
        target_is_dir = target.is_dir()
        target_has_files = target_is_dir and any(target.iterdir())
    except OSError as error:
        raise FileNotFoundError(
            f"Cannot access target folder {target}. Use '.' for the current folder."
        ) from error

    if target_exists and not target_is_dir:
        raise FileExistsError(f"{target} already exists and is not a folder.")

    if target_has_files and not force:
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
    (target / "assets" / "diagrams").mkdir(parents=True, exist_ok=True)
    return target


def init_git_repository(target: Path) -> None:
    git_dir = target / ".git"
    if git_dir.exists():
        return

    try:
        subprocess.run(
            ["git", "init"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise FileNotFoundError("git executable was not found") from error
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or "git init failed"
        raise RuntimeError(message) from error


def install_mermaid_cli(npm_executable: str) -> None:
    try:
        subprocess.run(
            [npm_executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise FileNotFoundError(
            "npm executable was not found. Install Node.js/npm first, then run this command again."
        ) from error
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or "npm check failed"
        raise RuntimeError(message) from error

    try:
        subprocess.run(
            [npm_executable, "install", "-g", "@mermaid-js/mermaid-cli"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or "Mermaid CLI installation failed"
        raise RuntimeError(message) from error


def validate_document_project(root: Path, required_folders: tuple[str, ...]) -> None:
    if not root.exists():
        raise FileNotFoundError(f"Document project does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Document project is not a folder: {root}")

    missing = [folder for folder in required_folders if not (root / folder).is_dir()]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(
            f"Invalid document project at {root}. Missing required folder(s): {joined}"
        )


def build_document(
    root: Path,
    output_format: str,
    output_name: str,
    title: str,
    footer: str,
    author: str,
    sections: str,
    dist: str,
    recursive: bool,
) -> list[Path]:
    validate_document_project(root, (sections, "assets"))
    source = root / sections
    output_dir = root / dist
    outputs: list[Path] = []

    if output_format in {"pdf", "all"}:
        outputs.append(
            build_pdf(
                source,
                output_dir / f"{output_name}.pdf",
                "*.md",
                recursive,
                title,
                footer,
                author,
            )
        )

    if output_format in {"docx", "all"}:
        outputs.append(build_docx(source, output_dir / f"{output_name}.docx", "*.md", recursive))

    return outputs


def render_diagrams(
    root: Path,
    renderer: str,
    source: str,
    output: str,
    pattern: str,
    recursive: bool,
    executable: str,
) -> list[Path]:
    validate_document_project(root, (source, "assets"))
    if renderer == "mermaid":
        return render_mermaid_diagrams(
            root / source,
            root / output,
            pattern,
            recursive,
            executable or "mmdc",
        )
    if renderer == "python":
        return render_python_diagrams(
            root,
            root / source,
            root / output,
            pattern,
            recursive,
            executable,
        )
    raise ValueError(f"Unsupported diagram renderer: {renderer}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="md2doc",
        description="Create and build Markdown-based PDF/DOCX document projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new document project.")
    init_parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Target folder for the document project. Default: current directory.",
    )
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
    init_parser.add_argument(
        "--git",
        action="store_true",
        help="Initialize the document folder as a Git repository.",
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
    build_parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Search Markdown files in section subfolders. Default: enabled.",
    )

    diagrams_parser = subparsers.add_parser(
        "diagrams",
        help="Render diagrams to image assets.",
    )
    diagrams_parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Document project root. Default: current directory.",
    )
    diagrams_parser.add_argument(
        "--renderer",
        choices=["mermaid", "python"],
        default="mermaid",
        help="Diagram renderer to use. Default: mermaid",
    )
    diagrams_parser.add_argument(
        "--source",
        default="diagrams",
        help="Diagram source folder. Default: diagrams",
    )
    diagrams_parser.add_argument(
        "--output",
        default="assets/diagrams",
        help="Rendered image output folder. Default: assets/diagrams",
    )
    diagrams_parser.add_argument(
        "--pattern",
        default="*.mmd",
        help="Diagram source pattern. Default: *.mmd",
    )
    diagrams_parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Search diagram source files in subfolders. Default: enabled.",
    )
    diagrams_parser.add_argument(
        "--executable",
        default=None,
        help="Renderer executable. Default: mmdc for Mermaid, current Python for Python.",
    )

    install_deps_parser = subparsers.add_parser(
        "install-deps",
        help="Install optional external dependencies used by md2doc.",
    )
    install_deps_parser.add_argument(
        "--npm",
        default="npm",
        help="npm executable used to install Mermaid CLI. Default: npm",
    )
    install_deps_parser.add_argument(
        "--skip-mermaid",
        action="store_true",
        help="Do not install Mermaid CLI.",
    )

    subparsers.add_parser("structure", help="Print the recommended Markdown structure.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        if args.command == "init":
            target = copy_template(args.target, args.template, args.force)
            if args.git:
                init_git_repository(target)
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
                args.recursive,
            )
            for output in outputs:
                print(output)
            return

        if args.command == "diagrams":
            outputs = render_diagrams(
                args.root,
                args.renderer,
                args.source,
                args.output,
                args.pattern,
                args.recursive,
                args.executable,
            )
            for output in outputs:
                print(output)
            return

        if args.command == "install-deps":
            if not args.skip_mermaid:
                install_mermaid_cli(args.npm)
                print("Installed Mermaid CLI.")
            return

        if args.command == "structure":
            from md2doc.pdf_builder import STRUCTURE_HELP

            print(STRUCTURE_HELP)
    except (
        FileExistsError,
        FileNotFoundError,
        NotADirectoryError,
        OSError,
        RuntimeError,
    ) as error:
        print(f"md2doc: error: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
