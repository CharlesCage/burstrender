import sys
from pathlib import Path

from imageautomation import binaries


def test_resolve_prefers_bundled(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    (bin_dir / "ffmpeg").mkdir(parents=True)
    bundled = bin_dir / "ffmpeg" / "ffmpeg"
    bundled.write_text("#!/bin/sh\n")
    monkeypatch.setattr(binaries, "bundle_bin_dir", lambda: bin_dir)
    monkeypatch.setattr(binaries, "_EXE_SUFFIX", "")

    assert binaries.resolve("ffmpeg") == str(bundled)


def test_resolve_falls_back_to_path(tmp_path, monkeypatch):
    monkeypatch.setattr(binaries, "bundle_bin_dir", lambda: tmp_path / "nope")
    monkeypatch.setattr(binaries.shutil, "which", lambda name: "/usr/bin/" + name if name == "ffmpeg" else None)

    assert binaries.resolve("ffmpeg") == "/usr/bin/ffmpeg"


def test_resolve_magick_falls_back_to_convert(tmp_path, monkeypatch):
    monkeypatch.setattr(binaries, "bundle_bin_dir", lambda: tmp_path / "nope")

    def fake_which(name):
        return "/usr/bin/convert" if name == "convert" else None

    monkeypatch.setattr(binaries.shutil, "which", fake_which)
    assert binaries.resolve("magick") == "/usr/bin/convert"


def test_resolve_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(binaries, "bundle_bin_dir", lambda: tmp_path / "nope")
    monkeypatch.setattr(binaries.shutil, "which", lambda name: None)
    assert binaries.resolve("rawtherapee-cli") is None
