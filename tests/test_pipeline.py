import imageautomation.pipeline as pl
from imageautomation import runtime as config


def _wire(monkeypatch, tmp_path, calls):
    config.working_directory = str(tmp_path)
    config.destination_path = str(tmp_path)
    monkeypatch.setattr(pl, "render_pngs_from_cr3s", lambda files, out, frame_progress=None: calls.append(("render", out)) or True)
    monkeypatch.setattr(pl, "create_mp4", lambda out, ls: calls.append(("mp4", out, ls)) or True)
    monkeypatch.setattr(pl, "stabilize_mp4", lambda out: calls.append(("stabilize", out)) or True)
    monkeypatch.setattr(pl, "create_gif_from_mp4", lambda out, ls, no_stab: calls.append(("gif", out, no_stab)) or True)
    monkeypatch.setattr(pl, "move_output_files", lambda out, mp4=True, stabilized=True, gif=True: calls.append(("move", mp4, stabilized, gif)) or True)
    monkeypatch.setattr(pl, "cleanup_files", lambda out: calls.append(("cleanup", out)) or True)


def test_gif_only_still_stabilizes_the_gif(monkeypatch, tmp_path):
    """v4 fidelity: --gif-only runs stabilization and feeds the GIF the
    stabilized MP4; it only suppresses SHIPPING the MP4s."""
    calls = []
    _wire(monkeypatch, tmp_path, calls)
    burst = [("/p/a.CR3", "width")] * 10

    assert pl.process_burst(burst, 0, output_mp4=False, output_stabilized=False, output_gif=True, stabilize=True) is True

    assert ("stabilize", "burst_1") in calls
    gif_call = next(c for c in calls if c[0] == "gif")
    assert gif_call[2] is False  # no_stabilization=False -> GIF from stabilized mp4
    move_call = next(c for c in calls if c[0] == "move")
    assert move_call[1:] == (False, False, True)  # ship only the gif


def test_no_stabilization_skips_pass_and_gif_uses_plain_mp4(monkeypatch, tmp_path):
    calls = []
    _wire(monkeypatch, tmp_path, calls)
    burst = [("/p/a.CR3", "width")] * 10

    assert pl.process_burst(burst, 0, output_mp4=True, output_stabilized=False, output_gif=True, stabilize=False) is True

    assert not any(c[0] == "stabilize" for c in calls)
    gif_call = next(c for c in calls if c[0] == "gif")
    assert gif_call[2] is True


def test_default_render_stabilizes_and_ships_everything(monkeypatch, tmp_path):
    calls = []
    _wire(monkeypatch, tmp_path, calls)
    burst = [("/p/a.CR3", "height")] * 10

    assert pl.process_burst(burst, 0) is True
    assert ("stabilize", "burst_1") in calls
    mp4_call = next(c for c in calls if c[0] == "mp4")
    assert mp4_call[2] == "height"  # current burst's orientation
    move_call = next(c for c in calls if c[0] == "move")
    assert move_call[1:] == (True, True, True)


def test_frame_progress_forwarded(monkeypatch, tmp_path):
    calls = []
    seen = []
    _wire(monkeypatch, tmp_path, calls)
    monkeypatch.setattr(
        pl, "render_pngs_from_cr3s",
        lambda files, out, frame_progress=None: (frame_progress and frame_progress(1, len(files))) or True,
    )
    pl.process_burst([("/p/a.CR3", "width")] * 3, 0, frame_progress=lambda c, t: seen.append((c, t)))
    assert seen == [(1, 3)]
