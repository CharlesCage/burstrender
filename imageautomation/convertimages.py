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
import subprocess

# Modules
from .utilities import PrintLog

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
    for cr3_file in tqdm(cr3_files, desc="Converting CR3s to PNGs", leave=False, disable=True if len(cr3_files) == 1 else config.quiet):
        try:
            completed_process = subprocess.run(
                [
                    f"convert",
                    f"{cr3_file}",
                    f"-auto-level",
                    f"-modulate",
                    f"{config.modulate_string}",
                    f"-gravity",
                    f"{config.gravity_string}",
                    f"-crop",
                    f"{config.crop_string}",
                    f"-resize",
                    f"2000",
                    f"{config.destination_path if len(cr3_files) == 1 else config.working_directory}/{output_file}-image_{format(cr3_files.index(cr3_file) + 1).zfill(3)}.png",
                ],
                check=True,
                capture_output=True,
            )

        except FileNotFoundError as exc:
            PrintLog.error(
                f"Failed to convert {cr3_file} to {output_file}.png "
                f"because the convert (ImageMagick) executable could not be found\n{exc}\n"
                f"Please ensure that ImageMagick is installed and the convert executable is in your PATH.\n"
                f"{exc.stderr.decode() if hasattr(exc, 'stderr') else ''}"
            )
            return False

        except subprocess.CalledProcessError as exc:
            PrintLog.error(
                f"Failed to convert {cr3_file} to {output_file}.png "
                f"because convert (ImageMagick) did not return a successful return code. "
                f"Returned {exc.returncode}\n{exc}\n"
                f"{exc.stderr.decode() if hasattr(exc, 'stderr') else ''}"
            )
            return False

        except subprocess.TimeoutExpired as exc:
            PrintLog.error(
                f"Failed to convert {cr3_file} to {output_file}.png "
                f"because process timed out.\n{exc}/n"
                f"{exc.stderr.decode() if hasattr(exc, 'stderr') else ''}"
            )
            return False
        
        PrintLog.debug(f"Converted {cr3_file} to {output_file}.png")

    return True
