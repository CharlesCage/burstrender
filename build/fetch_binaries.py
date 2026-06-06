"""Fetch, verify, and arrange the vendored Windows binaries.

Usage:
  python build/fetch_binaries.py            # verify checksums, arrange into build/vendor/bin/
  python build/fetch_binaries.py --pin      # first run: download, COMPUTE checksums, write them back

Downloads cache in build/vendor/cache/. Output layout in build/vendor/bin/
mirrors imageautomation.binaries.TOOLS bundle_rel paths:
  bin/exiftool/exiftool.exe (+ exiftool_files/)
  bin/ffmpeg/ffmpeg.exe
  bin/imagemagick/magick.exe  (+ DLLs, config files as siblings)
  bin/rawtherapee/rawtherapee-cli.exe (+ DLLs, share/)

Notes on extraction formats:
  - exiftool / ffmpeg / rawtherapee: standard zip
  - imagemagick: portable .7z (ImageMagick dropped the portable .zip format);
    requires 7z on PATH (pre-installed on GitHub Actions windows-latest and
    available as p7zip-full on Ubuntu).
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parent
MANIFEST = BUILD_DIR / "binaries.json"
CACHE = BUILD_DIR / "vendor" / "cache"
BIN = BUILD_DIR / "vendor" / "bin"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(name, spec):
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / Path(spec["url"]).name
    if not target.exists():
        print(f"[{name}] downloading {spec['url']}")
        urllib.request.urlretrieve(spec["url"], target)
    else:
        print(f"[{name}] cached: {target.name}")
    return target


def extract(name, spec, archive):
    workdir = CACHE / f"{name}-extracted"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    mode = spec["extract"]
    if mode == "zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(workdir)
    elif mode == "7z":
        seven_z = shutil.which("7z") or shutil.which("7za") or shutil.which("7zz")
        if not seven_z:
            raise SystemExit(
                f"[{name}] 7z extractor not found on PATH; "
                "install p7zip-full (Linux) or ensure 7z is available (Windows CI)"
            )
        subprocess.run(
            [seven_z, "x", str(archive), f"-o{workdir}", "-y"],
            check=True,
        )
    elif mode == "innoextract":
        subprocess.run(
            ["innoextract", "--extract", "--output-dir", str(workdir), str(archive)],
            check=True,
        )
    else:
        raise SystemExit(f"[{name}] unknown extract mode: {mode!r}")
    return workdir


def _find_src(name, src_rel, workdir):
    """Locate src_rel inside workdir.

    Special value '.': return workdir itself (copy the whole extracted root).
    Otherwise try:
      1. workdir / src_rel  (direct match)
      2. glob(src_rel)      (wildcard / pattern in root)
      3. glob(**/ src_rel)  (recursive search)
    """
    if src_rel == ".":
        return workdir
    direct = workdir / src_rel
    if direct.exists():
        return direct
    matches = list(workdir.glob(src_rel))
    if not matches:
        matches = list(workdir.glob(f"**/{src_rel}"))
    if not matches:
        raise SystemExit(f"[{name}] arrange source not found: {src_rel!r} in {workdir}")
    return matches[0]


def arrange(name, spec, workdir):
    for src_rel, dest_rel in spec["arrange"].items():
        src = _find_src(name, src_rel, workdir)
        dest = BIN / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"[{name}] {src.name}/ -> {dest_rel}/")
        else:
            shutil.copy2(src, dest)
            print(f"[{name}] {src.name} -> {dest_rel}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and arrange vendored Windows binaries for burstrender."
    )
    parser.add_argument(
        "--pin",
        action="store_true",
        help="compute sha256 for each download and write values back into binaries.json",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())

    for name, spec in manifest.items():
        archive = download(name, spec)
        digest = sha256_of(archive)
        if args.pin:
            spec["sha256"] = digest
            print(f"[{name}] pinned sha256={digest}")
        else:
            if not spec.get("sha256"):
                raise SystemExit(
                    f"[{name}] sha256 is empty in manifest — run with --pin first"
                )
            if spec["sha256"] != digest:
                raise SystemExit(
                    f"[{name}] CHECKSUM MISMATCH\n"
                    f"  expected {spec['sha256']}\n"
                    f"  got      {digest}"
                )
        workdir = extract(name, spec, archive)
        arrange(name, spec, workdir)

    if args.pin:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"manifest updated: {MANIFEST}")

    print(f"\nvendor bin ready: {BIN}")


if __name__ == "__main__":
    main()
