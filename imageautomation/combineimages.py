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

# Logging
from loguru import logger

# Config for global variables
import config

def create_mp4(output_file):
    """
    Create an MP4 file from the PNG files using FFmpeg.

    Parameters:

        output_file : str
            The base file name for the input PNG and output MP4 files

    Returns:

        bool
            True if the process was successful, False otherwise
    """

    # Execute command to create an MP4 file from the PNG files
    command = [
        f"ffmpeg",
        f"-i",
        f"{config.working_directory}/{output_file}-image_%03d.png",
        f"-vf",
        f"scale=2000:-2,setpts=2.0*PTS",
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

    # Execute command to perform stabilization analysis on the MP4 file
    command = [
                f"ffmpeg",
                f"-i",
                f"{config.working_directory}/{output_file}.mp4",
                f"-vf",
                f"vidstabdetect=shakiness=10:accuracy=15:result='{config.working_directory}/{output_file}.trf'",
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
                f"ffmpeg",
                f"-i",
                f"{config.working_directory}/{output_file}.mp4",
                f"-vf",
                f"vidstabtransform=smoothing=30:input='{config.working_directory}/{output_file}.trf'",
                f"{config.working_directory}/{output_file}-stabilized.mp4",
    ]

    result = run_subprocess(
        "ffmpeg",
        command,
        success_message=f"Stabilized {output_file}.mp4",
        error_message=f"Failed to stabilize {output_file}.mp4"
    )

    return result

def create_gif_from_mp4(output_file, no_stabilization=False):
    """
    Create a GIF file from the MP4 file using FFmpeg.

    Parameters:

            output_file : str
                The base file name (no ext) for the MP4 input and output files

            no_stabilization : bool
                True if the MP4 file is not stabilized, False otherwise
                Default is False

    Returns:

            bool
                True if the process was successful, False otherwise
    """
    # Execute command to create a GIF file from the MP4 file
    command = [
        f"ffmpeg",
        f"-i",
        f"{config.working_directory}/{output_file}{'' if no_stabilization else'-stabilized'}.mp4",
        f"-filter_complex",
        f"[0:v] fps=30,scale=480:-1,split [a][b];[a] palettegen [p];[b][p] paletteuse",
        f"{config.working_directory}/{output_file}.gif",
    ]

    result = run_subprocess(
        "ffmpeg",
        command,
        success_message=f"Created {output_file}.gif",
        error_message=f"Failed to create {output_file}.gif"
    )

    return result