from imageautomation import runtime


def test_runtime_defaults():
    assert runtime.exit_code == 0
    assert runtime.exit_reason == ""
    assert runtime.quiet is False
    assert runtime.seconds_between_bursts == 2
    assert runtime.min_burst_length == 10
    assert runtime.file_extension == ".cr3"
    assert runtime.crop_string is None
    assert runtime.gravity_string is None


def test_runtime_is_mutable():
    runtime.exit_code = 2
    assert runtime.exit_code == 2
    runtime.exit_code = 0
