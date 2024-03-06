"""
Combine images into videos and GIFs

Classes:


Functions:

    None

Variables:

    None

Global Variables (via config):

    config.quiet : bool
        Suppress progress bar output (default False)

"""

# History
# 2024-03-05 Initial version

# TODO
# None

#
# Imports
#

# General
import pandas as pd
import subprocess

# TUI progress bar
from tqdm import tqdm

# Logging
from loguru import logger

# Config for global variables
import config

def create_mp4(output_file):
    """
    Create an MP4 file from the PNG files using FFmpeg.

    Parameters:

        output_file : str
            The output file name for the MP4 file

    Returns:

        bool
            True if the process was successful, False otherwise
    """

    # Execute command to create an MP4 file from the PNG files
    try:
        completed_process = subprocess.run(
            [
                f"ffmpeg",
                f"-i",
                f"{output_file}-image_%03d.png",
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
                f"{output_file}.mp4",
            ],
            capture_output=True,
        )
        # Print "MP4 created" if the process was successful
        print(f"Created {output_file}.mp4")

        return True

    except FileNotFoundError as exc:
        print(f"Process failed because the executable could not be found.\n{exc}")
        return False

    except subprocess.CalledProcessError as exc:
        print(
            f"Process failed because did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}"
        )
        return False

    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")
        return False


def stabilize_mp4(output_file):
    """
    Stabilize the MP4 file using FFmpeg.

    Parameters:

        output_file : str
            The output file name for the MP4 file

    Returns:

        bool
            True if the process was successful, False otherwise
    """

    # Execute command to perform stabilization analysis on the MP4 file
    try:
        completed_process = subprocess.run(
            [
                f"ffmpeg",
                f"-i",
                f"{output_file}.mp4",
                f"-vf",
                f"vidstabdetect=shakiness=10:accuracy=15:result='{output_file}.trf'",
                f"-f",
                f"null",
                f"-",
            ],
            capture_output=True,
        )
        # Print "MP4 created" if the process was successful
        print(f"Created {output_file}.trf stabilization analysis file")

    except FileNotFoundError as exc:
        print(f"Process failed because the executable could not be found.\n{exc}")
        return False

    except subprocess.CalledProcessError as exc:
        print(
            f"Process failed because did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}"
        )
        return False

    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")
        return False

    # Execute command to stabilize the MP4 file
    try:
        completed_process = subprocess.run(
            [
                f"ffmpeg",
                f"-i",
                f"{output_file}.mp4",
                f"-vf",
                f"vidstabtransform=smoothing=30:input='{output_file}.trf'",
                f"{output_file}-stabilized.mp4",
            ],
            capture_output=True,
        )
        # Print "MP4 created" if the process was successful
        print(f"Created {output_file}-stabilized.mp4")
        return True

    except FileNotFoundError as exc:
        print(f"Process failed because the executable could not be found.\n{exc}")
        return False

    except subprocess.CalledProcessError as exc:
        print(
            f"Process failed because did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}"
        )
        return False

    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")
        return False


def create_gif_from_mp4(output_file):
    """
    Create a GIF file from the MP4 file using FFmpeg.

    Parameters:

            output_file : str
                The output file name for the GIF file

    Returns:

            bool
                True if the process was successful, False otherwise
    """
    # Execute command to create a GIF file from the MP4 file
    try:
        completed_process = subprocess.run(
            [
                f"ffmpeg",
                f"-i",
                f"{output_file}-stabilized.mp4",
                f"-filter_complex",
                f"[0:v] fps=30,scale=480:-1,split [a][b];[a] palettegen [p];[b][p] paletteuse",
                f"{output_file}.gif",
            ],
            capture_output=True,
        )
        # Print "GIF created" if the process was successful
        print(f"Created {output_file}.gif")
        return True

    except FileNotFoundError as exc:
        print(f"Process failed because the executable could not be found.\n{exc}")
        return False
    except subprocess.CalledProcessError as exc:
        print(
            f"Process failed because did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}"
        )
        return False
    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")
        return False
