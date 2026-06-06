import pandas as pd

from imageautomation.imagedata import detect_bursts


def _frame(ts, subsec, orientation=1, name="IMG_0001.CR3"):
    return {
        "SourceFile": f"/photos/{name}",
        "EXIF:DateTimeOriginal": ts,
        "EXIF:SubSecTimeOriginal": subsec,
        "EXIF:Orientation": orientation,
    }


def _burst_df():
    rows = []
    # Burst A: 12 frames, 0.1s apart, landscape
    for i in range(12):
        rows.append(_frame("2024:02:16 14:14:19", 10 * i, 1, f"A{i:03d}.CR3"))
    # Gap of ~5 minutes; Burst B: 11 frames, portrait (orientation 8)
    for i in range(11):
        rows.append(_frame("2024:02:16 14:19:30", 10 * i, 8, f"B{i:03d}.CR3"))
    # Straggler group: only 3 frames — below min_burst_length, dropped
    for i in range(3):
        rows.append(_frame("2024:02:16 14:25:00", 10 * i, 1, f"C{i:03d}.CR3"))
    return pd.DataFrame(rows)


def test_detect_bursts_groups_and_filters():
    result = detect_bursts(_burst_df(), False, 2, 10)
    assert len(result) == 2
    assert len(result[0]) == 12
    assert len(result[1]) == 11
    # Entries are (full_path, long_side) tuples
    path, long_side = result[0][0]
    assert path.endswith("A000.CR3")
    assert long_side == "width"
    assert result[1][0][1] == "height"  # portrait burst


def test_detect_bursts_detect_only_info():
    info = detect_bursts(_burst_df(), True, 2, 10)
    assert len(info) == 2
    assert info[0]["frames"] == 12
    assert info[0]["long_side"] == "width"
    assert info[1]["frames"] == 11
    assert info[1]["long_side"] == "height"


def test_detect_bursts_min_length_knob():
    info = detect_bursts(_burst_df(), True, 2, 3)
    assert len(info) == 3  # straggler group now qualifies
