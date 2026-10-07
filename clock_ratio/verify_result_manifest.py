#!/usr/bin/env python3
"""Independent checker CLI for the authoritative analysis manifest.

Re-reads the manifest bytes, re-runs every reconcile rule, and re-hashes the
inputs, parameters, and products on disk. Prints ``OK <path>`` on success and
exits non-zero with the error on stderr otherwise. This is the entry point the
downstream audit tasks invoke.
"""
from __future__ import annotations

import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock_ratio.result_manifest import (  # noqa: E402
    ManifestError,
    ResultManifest,
    read_manifest,
    verify_manifest,
)

REPO = Path(__file__).resolve().parents[1]


def verify_path(manifest_path: Path, *, root: Path) -> ResultManifest:
    manifest_path = Path(manifest_path)
    manifest = read_manifest(manifest_path)
    verify_manifest(manifest, root=Path(root), base_dir=manifest_path.parent)
    return manifest


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command()
def main(
    manifest: Path = typer.Argument(..., exists=True, dir_okay=False),
    root: Path = typer.Option(REPO, exists=True, file_okay=False),
) -> None:
    try:
        verify_path(manifest, root=root)
    except ManifestError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"OK {manifest}")


if __name__ == "__main__":
    app()
