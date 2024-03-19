"""
Convert images from one format to another

Classes:


Functions:

    render_pngs_from_cr3s

Variables:

    None

Global Variables (via config):

    config.quiet : bool
        Suppress progress bar output (default False)

"""

# History
# 2024-03-11 Remove auto-level, normalize, and modulate from initial PNG conversion
# 2024-03-11 Refactor render_pngs_from_cr3s to use run_subprocess
# 2024-03-11 Fix error handling in render_pngs_from_cr3s
# 2024-03-07 Add gravity_string to config
# 2024-03-07 Add crop_string to config
# 2024-03-07 Add modulate_string to config
# 2024-03-06 Add logging and quiet option
# 2024-03-06 Add tqdm progress bar, single-file processing, and working directory
# 2024-03-05 Firsts version

# TODO
# None

#
# Imports
#

# General

# Modules
from .utilities import PrintLog
from .utilities import run_subprocess

# TUI progress bar
from tqdm import tqdm

# Logging
from loguru import logger

# Config for global variables
import config


def render_pngs_from_cr3s(cr3_files, output_file):
    """
    Render PNG files from CR3 files using ImageMagick.

    Parameters:

        cr3_files : list
            A list of full path filenames of the CR3 files

        output_file : str
            The output file name for the PNG files

    Returns:

        bool
            True if the process was successful, False otherwise
    """

    # Loop through cr3_files and execute command to convert each CR3 file to a PNG file
    for cr3_file in tqdm(
        cr3_files,
        desc="Converting CR3s to PNGs",
        leave=False,
        disable=True if len(cr3_files) == 1 else config.quiet,
    ):
        command = [
            f"convert",
            f"{cr3_file}",
            f"-gravity",
            f"{config.gravity_string}",
            f"-crop",
            f"{config.crop_string}",
            f"-resize",
            f"2000",
            f"{config.destination_path if len(cr3_files) == 1 else config.working_directory}/{output_file}-image_{format(cr3_files.index(cr3_file) + 1).zfill(3)}.png",
        ]

        result = run_subprocess(
            "convert",
            command,
            f"Converted {cr3_file} to {output_file}.png",
            f"Failed to convert {cr3_file} to {output_file}.png",
        )

    return result

def apply_correction_to_gif(output_file):
    """
    Apply a correction to the GIF file using ImageMagick.

    Parameters:

        output_file : str
            The base file name for the input PNG and output GIF files

    Returns:

        bool
            True if the process was successful, False otherwise
    """

    # Execute command to apply a correction to the GIF file
    command = [
        f"convert",
        f"{config.working_directory}/{output_file}-uncorrected.gif",
        f"-auto-level",
        f"-normalize",
        f"-modulate",
        f"{config.modulate_string}",
        f"{config.working_directory}/{output_file}.gif",
    ]

    result = run_subprocess(
        "convert",
        command,
        f"Applied correction to {output_file}.gif",
        f"Failed to apply correction to {output_file}.gif",
    )

    return result
