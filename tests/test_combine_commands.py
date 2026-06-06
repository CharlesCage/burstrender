import imageautomation.combineimages as cm
from imageautomation import runtime as config


def _setup(monkeypatch, tmp_path, captured_commands):
    config.working_directory = str(tmp_path)
    config.normalize_string = ",normalize=blackpt=black:whitept=white:smoothing=50"
    config.custom_vf_string = ""
    monkeypatch.setattr(cm, "resolve", lambda tool: f"/fake/{tool}")
    return captured_commands.patch(cm)


def test_create_mp4_command(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)
    assert cm.create_mp4("burst_1", "width") is True
    app, cmd = calls[0]
    assert app == "ffmpeg"
    assert cmd[0] == "/fake/ffmpeg"
    assert cmd[cmd.index("-i") + 1] == f"{tmp_path}/burst_1-image_%03d.png"
    vf = cmd[cmd.index("-vf") + 1]
    assert vf.startswith("scale=2000:-2,setpts=2.0*PTS")
    assert "normalize=" in vf
    assert cmd[-1] == f"{tmp_path}/burst_1.mp4"


def test_stabilize_runs_two_passes(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)
    assert cm.stabilize_mp4("burst_1") is True
    assert len(calls) == 2
    assert "vidstabdetect" in calls[0][1][calls[0][1].index("-vf") + 1]
    assert "vidstabtransform" in calls[1][1][calls[1][1].index("-vf") + 1]
    assert calls[1][1][-1] == f"{tmp_path}/burst_1-stabilized.mp4"


def test_gif_uses_stabilized_input_by_default(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)
    assert cm.create_gif_from_mp4("burst_1", "width", False) is True
    cmd = calls[0][1]
    assert cmd[cmd.index("-i") + 1] == f"{tmp_path}/burst_1-stabilized.mp4"
    assert cmd[-1] == f"{tmp_path}/burst_1.gif"


def test_gif_unstabilized_input(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)
    cm.create_gif_from_mp4("burst_1", "width", True)
    cmd = calls[0][1]
    assert cmd[cmd.index("-i") + 1] == f"{tmp_path}/burst_1.mp4"


def test_run_subprocess_none_command_is_friendly_failure():
    from imageautomation.utilities import run_subprocess
    assert run_subprocess("sometool", [None, "-x"], "ok", "failed") is False
