from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg"}


def collect_mermaid_files(input_path: Path, pattern: str, recursive: bool) -> list[Path]:
    if not input_path.is_dir():
        raise FileNotFoundError(f"Diagrams folder does not exist: {input_path}")

    files = input_path.rglob(pattern) if recursive else input_path.glob(pattern)
    return sorted(path for path in files if path.is_file())


def collect_python_diagram_scripts(input_path: Path, pattern: str, recursive: bool) -> list[Path]:
    if not input_path.is_dir():
        raise FileNotFoundError(f"Python diagrams folder does not exist: {input_path}")

    files = input_path.rglob(pattern) if recursive else input_path.glob(pattern)
    return sorted(path for path in files if path.is_file() and path.name != "__init__.py")


def render_mermaid_diagrams(
    input_path: Path,
    output_path: Path,
    pattern: str,
    recursive: bool,
    executable: str,
) -> list[Path]:
    diagrams = collect_mermaid_files(input_path, pattern, recursive)
    if not diagrams:
        raise FileNotFoundError(
            f"No Mermaid files matching pattern {pattern!r} were found in {input_path}"
        )

    outputs: list[Path] = []
    for source in diagrams:
        relative = source.relative_to(input_path).with_suffix(".png")
        destination = output_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                [executable, "-i", str(source), "-o", str(destination)],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Mermaid CLI executable {executable!r} was not found. "
                "Install @mermaid-js/mermaid-cli or pass --executable."
            ) from error
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() or error.stdout.strip() or "Mermaid rendering failed"
            raise RuntimeError(f"{source}: {message}") from error

        outputs.append(destination)

    return outputs


def module_name_for_script(project_root: Path, script: Path) -> str:
    try:
        relative = script.relative_to(project_root)
    except ValueError as error:
        raise ValueError(f"{script} is not inside project root {project_root}") from error
    return ".".join(relative.with_suffix("").parts)


def collect_generated_images(output_path: Path) -> list[Path]:
    outputs: list[Path] = []
    if output_path.is_dir():
        outputs = sorted(
            path
            for path in output_path.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )

    if not outputs:
        raise FileNotFoundError(f"No generated diagram images were found in {output_path}")
    return outputs


def render_python_diagrams(
    project_root: Path,
    input_path: Path,
    output_path: Path,
    pattern: str,
    recursive: bool,
    python_executable: str | None = None,
) -> list[Path]:
    scripts = collect_python_diagram_scripts(input_path, pattern, recursive)
    if not scripts:
        raise FileNotFoundError(
            f"No Python diagram scripts matching pattern {pattern!r} were found in {input_path}"
        )

    executable = python_executable or sys.executable
    output_path.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "MD2DOC_PROJECT_ROOT": str(project_root),
            "MD2DOC_ASSETS_DIR": str(output_path),
            "MD2DOC_OUTPUT_DIR": str(output_path),
        }
    )
    runner = (
        "import runpy, sys; "
        "project_root = sys.argv[1]; "
        "module_name = sys.argv[2]; "
        "sys.path = [p for p in sys.path if p not in ('', project_root)]; "
        "sys.path.append(project_root); "
        "runpy.run_module(module_name, run_name='__main__')"
    )
    for script in scripts:
        module_name = module_name_for_script(project_root, script)
        try:
            subprocess.run(
                [executable, "-c", runner, str(project_root), module_name],
                cwd=project_root,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Python executable {executable!r} was not found") from error
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() or error.stdout.strip() or "Python diagram failed"
            raise RuntimeError(f"{script}: {message}") from error

    return collect_generated_images(output_path)
