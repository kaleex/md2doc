from __future__ import annotations

import subprocess
from pathlib import Path


def collect_mermaid_files(input_path: Path, pattern: str, recursive: bool) -> list[Path]:
    if not input_path.is_dir():
        raise FileNotFoundError(f"Diagrams folder does not exist: {input_path}")

    files = input_path.rglob(pattern) if recursive else input_path.glob(pattern)
    return sorted(path for path in files if path.is_file())


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
