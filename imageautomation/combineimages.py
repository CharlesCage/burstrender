"""
Combine images into videos and GIFs

Classes:


Functions:

    create_mp4
    stabilize_mp4
    create_gif_from_mp4

Variables:

    None

Global Variables (via config):

    config.quiet : bool
        Suppress progress bar output (default False)

    config.working_directory : str
        The working directory for the project

"""

# History
#
# 2024-03-29 Add long_side parameter to create_mp4
# 2024-03-29 Add long_side parameter to create_gif_from_mp4
# 2024-03-18 Remove support for final ImageMagick correction of GIF
# 2024-03-11 Update documentation
# 2024-03-11 Refactor to use run_subprocess
# 2024-03-06 Add logging and quiet option, fix misplaced return statements
# 2024-03-05 First version

# TODO
# None

#
# Imports
#

# General

# Modules
from .utilities import run_subprocess
from imageautomation.binaries import resolve

# Logging
from loguru import logger

# Config for global variables
from imageautomation import runtime as config

def create_mp4(output_file, long_side="width"):
    """
    Create an MP4 file from the PNG files using FFmpeg.

    Parameters:

        output_file : str
            The base file name for the input PNG and output MP4 files

        long_side : str
            The long side of the video (width or height)
            Default is width

    Returns:

        bool
            True if the process was successful, False otherwise
    """

    # Determine the scale string based on the long side
    if long_side == "width":
        scale_string = "2000:-2"
    else:
        scale_string = "-2:2000"

    # Execute command to create an MP4 file from the PNG files
    command = [
        resolve("ffmpeg"),
        f"-i",
        f"{config.working_directory}/{output_file}-image_%03d.png",
        f"-vf",
        f"scale={scale_string},setpts=2.0*PTS{config.normalize_string}{config.custom_vf_string}",
        f"-c:v",
        f"libx264",
        f"-pix_fmt",
        f"yuv420p",
        f"-profile",
        f"main",
        f"-crf",
        f"1",
        f"-preset",
        f"medium",
        f"-movflags",
        f"faststart",
        f"{config.working_directory}/{output_file}.mp4",
    ]
    
    result = run_subprocess(
        "ffmpeg",
        command,
        success_message=f"Created {output_file}.mp4",
        error_message=f"Failed to create {output_file}.mp4"
    )

    return result


def stabilize_mp4(output_file):
    """
    Stabilize the MP4 file using FFmpeg.

    Parameters:

        output_file : str
            The base file name (no ext) for the MP4 input and output files

    Returns:

        bool
            True if the process was successful, False otherwise
    """

    # FFmpeg's libavfilter uses ':' as an option separator.  On Windows,
    # drive-letter paths (e.g. C:\...) contain a bare ':' that the filter-graph
    # parser mis-reads as an option separator, even inside single-quoted values.
    # Fix: convert backslashes to forward-slashes and escape the drive-letter
    # colon as '\:' so the ffmpeg filtergraph parser treats it as a literal colon.
    # Example: C:\Users\foo\burst_1.trf → C\:/Users/foo/burst_1.trf
    # The path is used without surrounding quotes so that the '\:' escape applies.
    import re as _re
    raw_trf = f"{config.working_directory}/{output_file}.trf"
    trf_path = raw_trf.replace("\\", "/")
    trf_path = _re.sub(r"^([A-Za-z])(:/)", r"\1\\:/", trf_path)

    # Execute command to perform stabilization analysis on the MP4 file
    command = [
                resolve("ffmpeg"),
                f"-i",
                f"{config.working_directory}/{output_file}.mp4",
                f"-vf",
                f"vidstabdetect=shakiness=10:accuracy=15:result={trf_path}",
                f"-f",
                f"null",
                f"-",
    ]

    result = run_subprocess(
        "ffmpeg",
        command,
        success_message=f"Stabilization analysis complete for {output_file}.mp4",
        error_message=f"Failed to process stabilization analysis for {output_file}.mp4"
    )

    if not result:
        return False

    # Execute command to stabilize the MP4 file
    command = [
                resolve("ffmpeg"),
                f"-i",
                f"{config.working_directory}/{output_file}.mp4",
                f"-vf",
                f"vidstabtransform=smoothing=30:input={trf_path}",
                f"{config.working_directory}/{output_file}-stabilized.mp4",
    ]

    result = run_subprocess(
        "ffmpeg",
        command,
        success_message=f"Stabilized {output_file}.mp4",
        error_message=f"Failed to stabilize {output_file}.mp4"
    )

    return result

def create_gif_from_mp4(output_file, long_side="width", no_stabilization=False):
    """
    Create a GIF file from the MP4 file using FFmpeg.

    Parameters:

            output_file : str
                The base file name (no ext) for the MP4 input and output files

            long_side : str
                The long side of the video (width or height)
                Default is width

            no_stabilization : bool
                True if the MP4 file is not stabilized, False otherwise
                Default is False

    Returns:

            bool
                True if the process was successful, False otherwise
    """
    # Determine the scale string based on the long side
    if long_side == "width":
        scale_string = "480:-1"
    else:
        scale_string = "-1:480"

    # Execute command to create a GIF file from the MP4 file
    command = [
        resolve("ffmpeg"),
        f"-i",
        f"{config.working_directory}/{output_file}{'' if no_stabilization else'-stabilized'}.mp4",
        f"-filter_complex",
        f"[0:v] fps=30,scale={scale_string},split [a][b];[a] palettegen [p];[b][p] paletteuse",
        f"{config.working_directory}/{output_file}.gif",
    ]

    result = run_subprocess(
        "ffmpeg",
        command,
        success_message=f"Created {output_file}.gif",
        error_message=f"Failed to create {output_file}.gif"
    )

    return result