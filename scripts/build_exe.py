#!/usr/bin/env python3
"""Build a standalone Windows .exe for merge-pdf using PyInstaller.

Run this script with the merge-pdf conda environment active.

Usage
-----
    python scripts/build_exe.py              # onedir bundle (recommended)
    python scripts/build_exe.py --onefile    # single .exe file

Output
------
  onedir  -> dist/merge-pdf/   (share the whole folder with users)
  onefile -> dist/merge-pdf.exe
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = ROOT / "src" / "merge_pdf" / "app.py"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "pyinstaller"  # inside already-gitignored build/


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a standalone merge-pdf executable with PyInstaller."
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Pack everything into a single .exe (slower startup).",
    )
    args = parser.parse_args()

    # --- check PyInstaller ---
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed.\nRun:  pip install pyinstaller")
        sys.exit(1)

    # --- assemble PyInstaller command ---
    cmd: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "merge-pdf",
        "--noconsole",  # hide the console window for this GUI app
        "--clean",
        "--noconfirm",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
    ]

    if args.onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    cmd.append(str(ENTRY_POINT))

    # --- run PyInstaller ---
    print("\nRunning PyInstaller …")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print("\nPyInstaller failed (see output above).")
        sys.exit(result.returncode)

    # --- summary ---
    print()
    if args.onefile:
        exe = DIST_DIR / "merge-pdf.exe"
        print(f"Single-file exe  : {exe}")
    else:
        out_dir = DIST_DIR / "merge-pdf"
        print(f"Output folder    : {out_dir}")
        print("Share the entire folder with users (do not move the .exe out of it).")

    print("\nDone.")


if __name__ == "__main__":
    main()
