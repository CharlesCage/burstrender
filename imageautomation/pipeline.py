"""Orchestration shared by the CLI and the GUI.

The CLI's main() and the GUI both drive these three functions. All knobs
travel through imageautomation.runtime (imported as config), exactly as the
lower-level modules expect.
"""

from imageautomation import runtime as config
from imageautomation.combineimages import (
    create_gif_from_mp4,
    create_mp4,
    stabilize_mp4,
)
from imageautomation.convertimages import correct_sample_png, render_pngs_from_cr3s
from imageautomation.imagedata import detect_bursts, extractEXIF
from imageautomation.utilities import PrintLog, delete_files, move_files


def detect(source_path, file_extension, seconds_between_bursts, min_burst_length):
    """EXIF-scan a folder and return (burst_info, burst_files).

    burst_info  : list of dicts (frames/start/end/long_side) — display data
    burst_files : list of lists of (path, long_side) tuples — work data

    Both views come from one EXIF pass. Returns ([], []) when no files match.
    """
    df = extractEXIF(source_path, file_extension)
    if df.empty:
        return [], []
    burst_info = detect_bursts(
        df, True, seconds_between_bursts, min_burst_length
    )
    burst_files = detect_bursts(
        df, False, seconds_between_bursts, min_burst_length
    )
    return burst_info, burst_files


def cleanup_files(output_file):
    """Remove the PNG and TRF intermediates for one burst."""
    ok = delete_files(f"{config.working_directory}/{output_file}-image_*.png")
    ok = delete_files(f"{config.working_directory}/{output_file}-develop.png") and ok
    ok = delete_files(f"{config.working_directory}/{output_file}.trf") and ok
    return ok


def move_output_files(output_file, mp4=True, stabilized=True, gif=True):
    """Copy requested outputs from the working dir to the destination."""
    ok = True
    if mp4:
        ok = move_files(
            f"{config.working_directory}/{output_file}.mp4",
            f"{config.destination_path}/{output_file}.mp4",
        ) and ok
    if stabilized:
        ok = move_files(
            f"{config.working_directory}/{output_file}-stabilized.mp4",
            f"{config.destination_path}/{output_file}-stabilized.mp4",
        ) and ok
    if gif:
        ok = move_files(
            f"{config.working_directory}/{output_file}.gif",
            f"{config.destination_path}/{output_file}.gif",
        ) and ok
    return ok


def render_sample(burst_files, burst_index):
    """Render the corrected first-frame PNG for one burst to the destination.

    Writes {destination}/burst_{n}-testimage.png. Returns True on success.
    """
    output_file = f"burst_{burst_index + 1}"
    first = burst_files[burst_index][0]
    if not render_pngs_from_cr3s([first], output_file):
        return False
    if not correct_sample_png(output_file, first[1]):
        PrintLog.warning(f"Failed to correct sample PNG for {output_file}")
        return False
    return True


def process_burst(
    cr3_files,
    burst_index,
    output_mp4=True,
    output_stabilized=True,
    output_gif=True,
    stabilize=True,
    progress=None,
):
    """Render one burst end-to-end. Returns True if all requested outputs landed.

    stabilize: run the stabilization pass; output_stabilized controls only
        whether the stabilized MP4 is shipped to the destination. (v4 fidelity:
        --gif-only still stabilizes and builds the GIF from the stabilized MP4 —
        it only suppresses shipping the MP4s.)
    progress: optional callable(stage_label: str) invoked as each stage starts.
    """

    def _stage(label):
        if progress:
            progress(label)

    output_file = f"burst_{burst_index + 1}"
    # v4 defect fix: use THIS burst's orientation (v4 passed the first
    # burst's long_side to create_mp4 for every burst)
    long_side = cr3_files[0][1]

    _stage("Converting RAW frames")
    if not render_pngs_from_cr3s(cr3_files, output_file):
        PrintLog.info(f"Failed to render PNGs for {output_file}. Skipping.")
        cleanup_files(output_file)
        return False

    _stage("Creating MP4")
    if not create_mp4(output_file, long_side):
        PrintLog.error(f"Failed to create MP4 for {output_file}. Skipping.")
        cleanup_files(output_file)
        return False

    if stabilize:
        _stage("Stabilizing MP4")
        if not stabilize_mp4(output_file):
            PrintLog.error(f"Failed to stabilize MP4 for {output_file}.")
            move_output_files(output_file, output_mp4, False, False)
            cleanup_files(output_file)
            return False

    if output_gif:
        _stage("Creating GIF")
        if not create_gif_from_mp4(output_file, long_side, not stabilize):
            PrintLog.error(f"Failed to create GIF for {output_file}.")
            move_output_files(output_file, output_mp4, output_stabilized, False)
            cleanup_files(output_file)
            return False

    _stage("Moving output files")
    if not move_output_files(output_file, output_mp4, output_stabilized, output_gif):
        PrintLog.warning(f"Failed to move files for {output_file}")

    _stage("Cleaning up")
    cleanup_files(output_file)
    PrintLog.success(f"Completed {output_file}")
    return True
