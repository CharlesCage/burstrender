import imageautomation.convertimages as ci
from imageautomation import runtime as config


def _setup(monkeypatch, tmp_path, captured_commands):
    config.working_directory = str(tmp_path)
    config.destination_path = str(tmp_path)
    config.crop_string = None
    config.gravity_string = None
    config.normalize_string = ""
    config.custom_vf_string = ""
    config.quiet = True
    config.file_extension = ".cr3"
    monkeypatch.setattr(ci, "resolve", lambda tool: f"/fake/{tool}")
    return captured_commands.patch(ci)


def test_cr3_goes_through_rawtherapee_then_magick(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)

    ok = ci.render_pngs_from_cr3s([("/photos/IMG_001.CR3", "width")], "burst_1")

    assert ok is True
    assert len(calls) == 2
    rt_app, rt_cmd = calls[0]
    assert rt_app == "rawtherapee-cli"
    assert rt_cmd[0] == "/fake/rawtherapee-cli"
    assert rt_cmd[1:5] == ["-o", f"{tmp_path}/burst_1-develop.png", "-n", "-Y"]
    assert rt_cmd[5:] == ["-c", "/photos/IMG_001.CR3"]

    im_app, im_cmd = calls[1]
    assert im_app == "magick"
    assert im_cmd[0] == "/fake/magick"
    assert im_cmd[1] == f"{tmp_path}/burst_1-develop.png"
    # landscape defaults: SouthEast gravity, 6000x4000+0+0 crop, 2000 wide
    assert "-gravity" in im_cmd and im_cmd[im_cmd.index("-gravity") + 1] == "SouthEast"
    assert "-crop" in im_cmd and im_cmd[im_cmd.index("-crop") + 1] == "6000x4000+0+0"
    assert "-resize" in im_cmd and im_cmd[im_cmd.index("-resize") + 1] == "2000"
    assert im_cmd[-1] == f"{tmp_path}/burst_1-image_001.png"


def test_portrait_defaults(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)
    ci.render_pngs_from_cr3s([("/photos/IMG_002.CR3", "height")], "burst_1")
    im_cmd = calls[1][1]
    assert im_cmd[im_cmd.index("-gravity") + 1] == "NorthEast"
    assert im_cmd[im_cmd.index("-crop") + 1] == "4000x6000+0+0"
    assert im_cmd[im_cmd.index("-resize") + 1] == "x2000"


def test_jpg_skips_rawtherapee_and_default_crop(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)
    config.file_extension = ".jpg"
    ci.render_pngs_from_cr3s([("/photos/IMG_003.JPG", "width")], "burst_1")
    assert len(calls) == 1  # no rawtherapee step
    im_cmd = calls[0][1]
    assert im_cmd[1] == "/photos/IMG_003.JPG"
    assert "-gravity" not in im_cmd and "-crop" not in im_cmd


def test_numbering_across_files(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)
    files = [(f"/photos/IMG_{i:03d}.CR3", "width") for i in range(3)]
    ci.render_pngs_from_cr3s(files, "burst_2")
    outputs = [c[1][-1] for c in calls if c[0] == "magick"]
    assert outputs == [
        f"{tmp_path}/burst_2-image_001.png",
        f"{tmp_path}/burst_2-image_002.png",
        f"{tmp_path}/burst_2-image_003.png",
    ]


def test_failure_of_any_file_fails_burst(monkeypatch, tmp_path, captured_commands):
    calls = _setup(monkeypatch, tmp_path, captured_commands)

    real_fake = ci.run_subprocess

    def failing_first_rt(application, command, success_message=None, error_message=None):
        if application == "rawtherapee-cli" and "IMG_000" in " ".join(command):
            return False
        return real_fake(application, command, success_message, error_message)

    monkeypatch.setattr(ci, "run_subprocess", failing_first_rt)
    files = [(f"/photos/IMG_{i:03d}.CR3", "width") for i in range(2)]
    assert ci.render_pngs_from_cr3s(files, "burst_1") is False


def test_frame_progress_called_per_file(monkeypatch, tmp_path, captured_commands):
    _setup(monkeypatch, tmp_path, captured_commands)
    seen = []
    files = [(f"/photos/IMG_{i:03d}.CR3", "width") for i in range(3)]
    ci.render_pngs_from_cr3s(files, "burst_3", frame_progress=lambda c, t: seen.append((c, t)))
    assert seen == [(1, 3), (2, 3), (3, 3)]
