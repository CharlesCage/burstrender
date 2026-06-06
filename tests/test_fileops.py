from pathlib import Path

import imageautomation.utilities as u
from imageautomation.utilities import delete_files, move_files


def test_delete_files_glob(tmp_path):
    (tmp_path / "a.png").write_text("x")
    (tmp_path / "b.png").write_text("x")
    (tmp_path / "keep.txt").write_text("x")

    assert delete_files(str(tmp_path / "*.png")) is True
    assert sorted(p.name for p in tmp_path.iterdir()) == ["keep.txt"]


def test_delete_files_no_match_is_success(tmp_path):
    # rm-on-nothing was tolerated before (treated as success); preserve that
    assert delete_files(str(tmp_path / "*.gif")) is True


def test_delete_files_refuses_root():
    assert delete_files("/") is False
    assert delete_files("/home") is False


def test_move_files_copy_default(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_text("data")
    dest = tmp_path / "out" / "dest.mp4"
    dest.parent.mkdir()

    assert move_files(str(src), str(dest)) is True
    assert dest.read_text() == "data"
    assert src.exists()  # copy=True is the historical default


def test_move_files_actual_move(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_text("data")
    dest = tmp_path / "dest.mp4"

    assert move_files(str(src), str(dest), copy=False) is True
    assert dest.read_text() == "data"
    assert not src.exists()


def test_move_files_missing_source_fails(tmp_path):
    assert move_files(str(tmp_path / "nope.mp4"), str(tmp_path / "d.mp4")) is False


def test_move_files_handles_quote_in_path(tmp_path):
    # The historical sh -c implementation broke on quotes — the TODO bug
    src = tmp_path / "it's a file.mp4"
    src.write_text("data")
    dest = tmp_path / "it's a dest.mp4"

    assert move_files(str(src), str(dest)) is True
    assert dest.read_text() == "data"


def test_subprocess_window_kwargs_platform(monkeypatch):
    monkeypatch.setattr(u.sys, "platform", "linux", raising=False)
    assert u._subprocess_window_kwargs() == {}

    monkeypatch.setattr(u.sys, "platform", "win32", raising=False)
    kwargs = u._subprocess_window_kwargs()
    assert "creationflags" in kwargs
