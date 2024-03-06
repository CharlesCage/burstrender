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
# 2024-03-05 Initial version

# TODO
# None

#
# Imports
#

# General
import subprocess

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
    for cr3_file in tqdm(cr3_files, desc="Converting CR3 to PNG", disable=True if len(cr3_files) == 1 else config.quiet):
        try:
            completed_process = subprocess.run(
                [
                    f"convert",
                    f"{cr3_file}",
                    f"-auto-level",
                    f"-modulate",
                    f"120",
                    f"-gravity",
                    f"SouthEast",
                    f"-crop",
                    f"6000x4000+0+0",
                    f"-resize",
                    f"2000",
                    f"{config.destination_path}/{output_file}-image_{format(cr3_files.index(cr3_file) + 1).zfill(3)}.png",
                ],
                capture_output=True,
            )

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

    return True
