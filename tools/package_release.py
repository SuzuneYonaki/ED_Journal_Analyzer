"""package_release.py - Builds the distributable release ZIP.

Run this AFTER `pyinstaller ED_Journal_Analyzer.spec` has produced
dist/ED_Journal_Analyzer.exe. This script does not invoke PyInstaller
itself; it only assembles the release archive.

Addons are shipped as plain, editable files alongside the exe (not baked
into the PyInstaller bundle), since the whole point of the addon system is
that addon.py files stay hot-editable without a rebuild. All addons ship
disabled by default (see each addons/<id>/addon.json's
"enabled_by_default": false) -- users opt in via Settings > Addons.

Usage:
    python tools/package_release.py [--version X.Y.Z]

Produces: dist/ED_Journal_Analyzer_v<version>.zip containing:
    ED_Journal_Analyzer.exe
    addons/<id>/addon.json
    addons/<id>/addon.py
    addons/<id>/ui/... (if present)
    addons/README.md

Dev-only addons (DEV_ONLY_ADDON_IDS, e.g. sample_hello) are intentionally
excluded -- they exist to exercise the addon mechanism during development
and have no value to an end user.
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIST_DIR = REPO / "dist"
EXE_NAME = "ED_Journal_Analyzer.exe"
ADDONS_SRC = REPO / "addons"

# Dev-only addons that exist purely to exercise the addon mechanism during
# development -- never useful to an end user, so excluded from releases.
DEV_ONLY_ADDON_IDS = {"sample_hello"}


def read_app_version() -> str:
    config_text = (REPO / "app" / "config.py").read_text(encoding="utf-8")
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', config_text)
    if not m:
        raise SystemExit("Could not find APP_VERSION in app/config.py")
    return m.group(1)


def iter_addon_files():
    """Yields (source_path, arcname) for every file that should ship under
    addons/ in the release zip. Skips __pycache__, other dev-only cruft, and
    DEV_ONLY_ADDON_IDS (e.g. sample_hello)."""
    if not ADDONS_SRC.is_dir():
        return
    for path in sorted(ADDONS_SRC.rglob("*")):
        if path.is_dir():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix == ".pyc":
            continue
        rel = path.relative_to(ADDONS_SRC)
        if rel.parts and rel.parts[0] in DEV_ONLY_ADDON_IDS:
            continue
        arcname = str(Path("addons") / rel)
        yield path, arcname


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="Override the version in the zip filename (default: app/config.py APP_VERSION)")
    args = parser.parse_args()

    version = args.version or read_app_version()
    exe_path = DIST_DIR / EXE_NAME
    if not exe_path.is_file():
        raise SystemExit(
            f"{exe_path} not found. Build it first with:\n"
            f"  pyinstaller ED_Journal_Analyzer.spec"
        )

    addon_files = list(iter_addon_files())
    if not addon_files:
        print(f"[package_release] WARNING: no files found under {ADDONS_SRC} -- zip will ship without addons/")

    out_path = DIST_DIR / f"ED_Journal_Analyzer_v{version}.zip"
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe_path, EXE_NAME)
        for src, arcname in addon_files:
            zf.write(src, arcname)

    print(f"[package_release] Wrote {out_path}")
    print(f"[package_release]   1 exe + {len(addon_files)} addon file(s)")


if __name__ == "__main__":
    main()
