from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from md2doc import cli
from md2doc.diagrams import (
    collect_mermaid_files,
    collect_python_diagram_scripts,
    render_mermaid_diagrams,
    render_python_diagrams,
)
from md2doc.docx_builder import build_docx
from md2doc.docx_builder import collect_markdown_files as collect_docx_markdown_files
from md2doc.pdf_builder import collect_markdown_files as collect_pdf_markdown_files


class InaccessibleTarget:
    def exists(self) -> bool:
        return True

    def is_dir(self) -> bool:
        return True

    def iterdir(self):
        raise OSError("cannot scan target")


class CliTests(unittest.TestCase):
    def test_copy_template_reports_inaccessible_target(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Cannot access target folder"):
            cli.copy_template(InaccessibleTarget(), "default", False)

    def test_main_prints_cli_error_for_file_system_errors(self) -> None:
        stderr = io.StringIO()

        with (
            patch.object(sys, "argv", ["md2doc", "init", "."]),
            patch.object(cli, "copy_template", side_effect=FileNotFoundError("bad target")),
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as exit_context,
        ):
            cli.main()

        self.assertEqual(exit_context.exception.code, 1)
        self.assertIn("md2doc: error: bad target", stderr.getvalue())

    def test_build_command_searches_sections_recursively_by_default(self) -> None:
        stdout = io.StringIO()
        with (
            patch.object(sys, "argv", ["md2doc", "build"]),
            patch.object(cli, "build_pdf", return_value=Path("dist/document.pdf")) as build_pdf,
            patch.object(cli, "build_docx", return_value=Path("dist/document.docx")) as build_docx,
            contextlib.redirect_stdout(stdout),
        ):
            cli.main()

        self.assertTrue(build_pdf.call_args.args[3])
        self.assertTrue(build_docx.call_args.args[3])

    def test_init_command_can_initialize_git_repository(self) -> None:
        stdout = io.StringIO()

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(sys, "argv", ["md2doc", "init", tmp, "--git"]),
            patch.object(cli, "copy_template", return_value=Path(tmp)) as copy_template,
            patch.object(cli, "init_git_repository") as init_git_repository,
            contextlib.redirect_stdout(stdout),
        ):
            cli.main()

        copy_template.assert_called_once()
        init_git_repository.assert_called_once_with(Path(tmp))

    def test_init_git_repository_skips_existing_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()

            with patch.object(cli.subprocess, "run") as run:
                cli.init_git_repository(root)

        run.assert_not_called()

    def test_main_prints_cli_error_when_git_init_fails(self) -> None:
        stderr = io.StringIO()

        with (
            patch.object(sys, "argv", ["md2doc", "init", ".", "--git"]),
            patch.object(cli, "copy_template", return_value=Path(".")),
            patch.object(cli, "init_git_repository", side_effect=RuntimeError("git failed")),
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as exit_context,
        ):
            cli.main()

        self.assertEqual(exit_context.exception.code, 1)
        self.assertIn("md2doc: error: git failed", stderr.getvalue())

    def test_install_mermaid_cli_uses_npm(self) -> None:
        with patch.object(cli.subprocess, "run") as run:
            cli.install_mermaid_cli("npm")

        self.assertEqual(run.call_args_list[0].args[0], ["npm", "--version"])
        self.assertEqual(
            run.call_args_list[1].args[0],
            ["npm", "install", "-g", "@mermaid-js/mermaid-cli"],
        )

    def test_install_deps_command_can_skip_mermaid(self) -> None:
        with (
            patch.object(sys, "argv", ["md2doc", "install-deps", "--skip-mermaid"]),
            patch.object(cli, "install_mermaid_cli") as install_mermaid,
        ):
            cli.main()

        install_mermaid.assert_not_called()

    def test_build_validates_document_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()

            with self.assertRaisesRegex(FileNotFoundError, "Missing required folder"):
                cli.build_document(
                    root,
                    "all",
                    "document",
                    "Title",
                    "Footer",
                    "Author",
                    "sections",
                    "dist",
                    True,
                )

    def test_diagrams_command_renders_mermaid_recursively(self) -> None:
        stdout = io.StringIO()

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(sys, "argv", ["md2doc", "diagrams", tmp]),
            patch.object(
                cli,
                "render_mermaid_diagrams",
                return_value=[Path(tmp) / "assets" / "diagrams" / "a.png"],
            ) as render_mermaid,
            contextlib.redirect_stdout(stdout),
        ):
            root = Path(tmp)
            (root / "diagrams").mkdir()
            (root / "assets").mkdir()
            cli.main()

        self.assertEqual(render_mermaid.call_args.args[0], Path(tmp) / "diagrams")
        self.assertEqual(render_mermaid.call_args.args[1], Path(tmp) / "assets" / "diagrams")
        self.assertTrue(render_mermaid.call_args.args[3])

    def test_diagrams_command_can_use_python_renderer(self) -> None:
        stdout = io.StringIO()

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(
                sys,
                "argv",
                [
                    "md2doc",
                    "diagrams",
                    tmp,
                    "--renderer",
                    "python",
                    "--source",
                    "tools/diagrams",
                    "--output",
                    "assets",
                    "--pattern",
                    "*.py",
                ],
            ),
            patch.object(
                cli,
                "render_python_diagrams",
                return_value=[Path(tmp) / "assets" / "diagram.png"],
            ) as render_python,
            contextlib.redirect_stdout(stdout),
        ):
            root = Path(tmp)
            (root / "tools" / "diagrams").mkdir(parents=True)
            (root / "assets").mkdir()
            cli.main()

        self.assertEqual(render_python.call_args.args[0], Path(tmp))
        self.assertEqual(render_python.call_args.args[1], Path(tmp) / "tools" / "diagrams")
        self.assertEqual(render_python.call_args.args[2], Path(tmp) / "assets")


class MarkdownCollectionTests(unittest.TestCase):
    def test_collect_markdown_files_can_search_subfolders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "00_intro.md").write_text("# Intro", encoding="utf-8")
            (root / "01_nested").mkdir()
            (root / "01_nested" / "00_detail.md").write_text("# Detail", encoding="utf-8")

            pdf_files = collect_pdf_markdown_files(root, "*.md", recursive=True)
            docx_files = collect_docx_markdown_files(root, "*.md", recursive=True)

        expected = [root / "00_intro.md", root / "01_nested" / "00_detail.md"]
        self.assertEqual(pdf_files, expected)
        self.assertEqual(docx_files, expected)

    def test_collect_markdown_files_can_ignore_subfolders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "00_intro.md").write_text("# Intro", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "01_detail.md").write_text("# Detail", encoding="utf-8")

            pdf_files = collect_pdf_markdown_files(root, "*.md", recursive=False)
            docx_files = collect_docx_markdown_files(root, "*.md", recursive=False)

        expected = [root / "00_intro.md"]
        self.assertEqual(pdf_files, expected)
        self.assertEqual(docx_files, expected)


class MermaidRenderingTests(unittest.TestCase):
    def test_collect_mermaid_files_can_search_subfolders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "00_context.mmd").write_text("flowchart TD", encoding="utf-8")
            (root / "01_nested").mkdir()
            (root / "01_nested" / "00_detail.mmd").write_text("flowchart TD", encoding="utf-8")

            files = collect_mermaid_files(root, "*.mmd", recursive=True)

        expected = [root / "00_context.mmd", root / "01_nested" / "00_detail.mmd"]
        self.assertEqual(files, expected)

    def test_render_mermaid_preserves_relative_subfolders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "diagrams"
            output = root / "assets" / "diagrams"
            (source / "01_nested").mkdir(parents=True)
            (source / "01_nested" / "00_detail.mmd").write_text(
                "flowchart TD\nA-->B",
                encoding="utf-8",
            )

            def fake_run(command, **_kwargs):
                Path(command[4]).write_text("png", encoding="utf-8")

            with patch("md2doc.diagrams.subprocess.run", side_effect=fake_run) as run:
                outputs = render_mermaid_diagrams(source, output, "*.mmd", True, "mmdc")

        self.assertEqual(outputs, [output / "01_nested" / "00_detail.png"])
        run.assert_called_once()


class PythonDiagramRenderingTests(unittest.TestCase):
    def test_collect_python_scripts_ignores_package_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "__init__.py").write_text("", encoding="utf-8")
            (root / "network.py").write_text("def main(): pass", encoding="utf-8")

            files = collect_python_diagram_scripts(root, "*.py", recursive=True)

        self.assertEqual(files, [root / "network.py"])

    def test_render_python_diagrams_reads_images_generated_in_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tools" / "diagrams"
            output = root / "assets"
            source.mkdir(parents=True)
            (root / "tools" / "__init__.py").write_text("", encoding="utf-8")
            (source / "__init__.py").write_text("", encoding="utf-8")
            (source / "network.py").write_text("def main(): pass", encoding="utf-8")

            def fake_run(_command, **kwargs):
                target = Path(kwargs["env"]["MD2DOC_OUTPUT_DIR"])
                (target / "network.png").write_text("png", encoding="utf-8")

            with patch("md2doc.diagrams.subprocess.run", side_effect=fake_run) as run:
                outputs = render_python_diagrams(root, source, output, "*.py", True)

        self.assertEqual(outputs, [output / "network.png"])
        run.assert_called_once()


class DocxRenderingTests(unittest.TestCase):
    def test_note_callout_does_not_render_marker_literal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sections"
            source.mkdir()
            (source / "00_note.md").write_text(
                "> [!NOTE] Important\n> Callout body.\n",
                encoding="utf-8",
            )
            output = root / "dist" / "document.docx"

            build_docx(source, output, "*.md", recursive=True)

            with zipfile.ZipFile(output) as docx:
                xml = docx.read("word/document.xml").decode("utf-8")

        self.assertIn("Important", xml)
        self.assertIn("Callout body.", xml)
        self.assertNotIn("[!NOTE]", xml)


if __name__ == "__main__":
    unittest.main()
