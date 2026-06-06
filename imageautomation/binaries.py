"""Resolution of the four external binaries burstrender drives.

Lookup order per tool:
  1. The bundle's bin/ directory (PyInstaller one-dir layout: exe-adjacent
     ``bin/<tool-subdir>/<exe>``; in a source checkout, ``<repo>/bin/...``).
  2. PATH (``shutil.which``), including fallback names (magick -> convert).

``doctor()`` prints what resolved where, with versions — the first
diagnostic to request when anything misbehaves.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from imageautomation.utilities import _subprocess_window_kwargs

# bundle_rel paths mirror how build/fetch_binaries.py arranges vendor files.
TOOLS = {
    "exiftool": {
        "bundle_rel": "exiftool/exiftool",
        "path_names": ["exiftool"],
        "version_args": ["-ver"],
    },
    "ffmpeg": {
        "bundle_rel": "ffmpeg/ffmpeg",
        "path_names": ["ffmpeg"],
        "version_args": ["-version"],
    },
    "magick": {
        "bundle_rel": "imagemagick/magick",
        "path_names": ["magick", "convert"],
        "version_args": ["-version"],
    },
    "rawtherapee-cli": {
        "bundle_rel": "rawtherapee/rawtherapee-cli",
        "path_names": ["rawtherapee-cli"],
        "version_args": ["--version"],
    },
}

_EXE_SUFFIX = ".exe" if sys.platform == "win32" else ""


def bundle_bin_dir():
    """Directory holding vendored binaries.

    Frozen layout (PyInstaller ≥6 one-dir):
      Primary:   <exe-dir>/bin/            (user-placed override or legacy layout)
      Fallback:  <exe-dir>/_internal/bin/  (PI6 places Tree() datas under _internal/)
    Source layout: <repo-root>/bin/
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        primary = exe_dir / "bin"
        if primary.exists():
            return primary
        return exe_dir / "_internal" / "bin"
    return Path(__file__).resolve().parent.parent / "bin"


def resolve(tool):
    """Return the full path to *tool* or None if unavailable."""
    spec = TOOLS[tool]
    bundled = bundle_bin_dir() / (spec["bundle_rel"] + _EXE_SUFFIX)
    if bundled.exists():
        return str(bundled)
    for name in spec["path_names"]:
        found = shutil.which(name)
        if found:
            return found
    return None


def _probe_version(tool, path):
    spec = TOOLS[tool]
    try:
        proc = subprocess.run(
            [path] + spec["version_args"],
            capture_output=True, text=True, timeout=15,
            **_subprocess_window_kwargs(),
        )
        out = (proc.stdout or proc.stderr).strip().splitlines()
        return out[0] if out else "(no version output)"
    except Exception as exc:  # version probe must never crash doctor
        return f"(version probe failed: {exc})"


def doctor():
    """Print resolution status for every tool. Returns True if all found."""
    frozen = getattr(sys, "frozen", False)
    print(f"burstrender doctor — platform={sys.platform} frozen={frozen}")
    print(f"bundle bin dir: {bundle_bin_dir()}")
    all_ok = True
    for tool in TOOLS:
        path = resolve(tool)
        if path is None:
            print(f"  [MISSING] {tool}: not found in bundle or PATH")
            all_ok = False
        else:
            print(f"  [OK]      {tool}: {path}")
            print(f"            {_probe_version(tool, path)}")
    return all_ok
