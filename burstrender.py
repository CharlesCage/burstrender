# History
#
# 1.0 - 2024-03-04 - Initial version

# TODO
# Add configuration file for working directory
# Add logging
# Add error handling
# Add command line arguments
# Add progress bars
# Add quiet mode


#
# Imports
#

# General
import os
import pandas as pd
import subprocess
import argparse

# Modules
from imageautomation.imagedata import extractEXIF
from imageautomation.imagedata import detect_bursts
from imageautomation.combineimages import create_mp4
from imageautomation.combineimages import stabilize_mp4
from imageautomation.combineimages import create_gif_from_mp4
from imageautomation.convertimages import render_pngs_from_cr3s

# TUI progress bar
from tqdm import tqdm

# Logging
from loguru import logger

# Config for global variables
import config

# VERSION
version = "1.0"
config.exit_code = 0
config.exir_reason = ""

#
# Set Up Logging
#

# Clear default logger sinks
logger.remove()

# Add sink for log file
logger.add(
    "logs/burstrender.log",
    rotation="10 MB",
    retention=10,
    backtrace=True,
    diagnose=True,
)

#
# Functions
#


def cleanup_files(output_file):
    """
    Remove the PNG and TRF files created during the rendering process.

    Parameters:

        output_file : str
            The best filename for the group output (ex. "burst_1")

    Returns:

        None
    """

    # Execute command to remove the PNG files
    try:
        completed_process = subprocess.run(
            [
                f"sh",
                f"-c",
                f"rm {output_file}-image_*.png",
            ],
            capture_output=True,
        )
        # Print "PNG files removed" if the process was successful
        print(f"Removed PNG files")

    except FileNotFoundError as exc:
        print(f"Process failed because the executable could not be found.\n{exc}")
    except subprocess.CalledProcessError as exc:
        print(
            f"Process failed because did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}"
        )
    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")

    # Execute command to remove the TRF file
    try:
        completed_process = subprocess.run(
            [
                f"sh",
                f"-c",
                f"rm {output_file}.trf",
            ],
            capture_output=True,
        )
        # Print "TRF file removed" if the process was successful
        print(f"Removed TRF file")

    except FileNotFoundError as exc:
        print(f"Process failed because the executable could not be found.\n{exc}")
    except subprocess.CalledProcessError as exc:
        print(
            f"Process failed because did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}"
        )
    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")


def main(args):
    """
    Main function to render burst photos to MP4s, Stabilized MP4s, and GIFs.
    """
    #
    # Set global variables
    #

    # Set the source path for the input CR3 files
    if args.source_path:
        config.source_path = args.source_path
    else:
        # source_path = os.getcwd()
        config.source_path = "/home/chuckcage/Insync/chuckcage@corporation3355.org/Google Drive/SportsPhotos/Burst Photos"

    # Set the destination path for the rendered videos and/or gifs
    if args.destination_path:
        config.destination_path = args.destination_path
    else:
        config.destination_path = os.getcwd()

    # Set the minimum time between detected bursts in seconds
    if args.seconds_between_bursts:
        seconds_between_bursts = args.seconds_between_bursts
    else:
        seconds_between_bursts = 2

    # Set the minimum number of photos in burst
    if args.minimum_burst_length:
        min_burst_length = args.minimum_burst_length
    else:
        min_burst_length = 10

    #
    # Process images
    #

    # Call the extractEXIF function to extract EXIF data from the images
    df = extractEXIF(config.source_path)

    # Exit if no CR3 files are found
    if df.empty:
        print(f"No CR3 files found in the source path: {config.ource_path}")
        print(f"Use the --source-path argument to specify a different source path.")
        exit()

    # Call the detect_bursts function to detect burst photo groups
    if args.detect_only:
        burst_info = detect_bursts(df, True, seconds_between_bursts, min_burst_length)

        print(f"Detected {len(burst_info)} burst(s):")
        for burst in burst_info:
            print(
                f"  Burst {burst_info.index(burst) + 1}: {burst['start']} to {burst['end']} ({burst['frames']} photos)"
            )
        exit()
    else:
        cr3_files_list = detect_bursts(
            df, False, seconds_between_bursts, min_burst_length
        )

    # Output sample images and exit if requested
    if args.sample_images_only:

        # Iterate over each group of CR3 files and output the first image of each burst
        for cr3_files in tqdm(cr3_files_list, desc="Rendering PNGs", unit="burst"):
            # Get the output file path for the PNG
            output_file = "burst_{}".format(cr3_files_list.index(cr3_files) + 1)

            # Render PNGs from CR3 files
            if not render_pngs_from_cr3s([cr3_files[0]], output_file):
                continue

        # Done
        exit()

    # Iterate over each group of CR3 files
    for cr3_files in cr3_files_list:
        # Get the output file path for the GIF
        output_file = "burst_{}".format(cr3_files_list.index(cr3_files) + 1)

        # Render PNGs from CR3 files
        if not render_pngs_from_cr3s(cr3_files, output_file):
            cleanup_files(output_file)
            continue

        # Create MP4 from PNGs
        if not create_mp4(output_file):
            cleanup_files(output_file)
            continue

        # Stabilize MP4
        if not stabilize_mp4(output_file):
            cleanup_files(output_file)
            continue

        # Create GIF from MP4
        if not create_gif_from_mp4(output_file):
            cleanup_files(output_file)
            continue

        # Cleanup files
        cleanup_files(output_file)
        print(
            f"Done with burst {cr3_files_list.index(cr3_files) + 1} of {len(cr3_files_list)}"
        )

        # exit()


# Run main function
if __name__ == "__main__":
    #
    # Build command line argument parser
    #

    parser = argparse.ArgumentParser(
        prog="burstrender",
        description="Render MP4s, Stabilized MP4s, and GIFs from burst CR3 RAW photos.",
        epilog="By Chuck Cage (chuckcage@corporation3355.org)",
    )

    parser.add_argument(
        "--source-path",
        action="store",
        help="Specify a source path for the input CR3 files. (If omitted, the current working directory is used.)",
    )

    parser.add_argument(
        "--destination-path",
        action="store",
        help="Specify a destination path for rendered videos and/or gifs. (If omitted, the current working directory is used.)",
    )

    parser.add_argument(
        "--seconds-between-bursts",
        action="store",
        help="Specify minimum time between detected bursts in seconds. (Default is 2.)",
    )

    parser.add_argument(
        "--minimum-burst-length",
        action="store",
        help="Specify minimum number of photos in burst. (Default is 10.)",
    )

    parser.add_argument(
        "--detect-only",
        action="store_true",
        help="Detect burst photos and display information only",
    )

    parser.add_argument(
        "--sample-images-only",
        action="store_true",
        help="Render the PNG for first image of each burst only",
    )

    parser.add_argument(
        "-ns",
        "--no-stabilization",
        action="store_true",
        help="Do not stabilize the images",
    )

    parser.add_argument(
        "-go",
        "--gif-only",
        action="store_true",
        help="Keep only final GIF and remove prelim MP4 files",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress bars",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + version,
        help="Show program version",
    )

    args = parser.parse_args()

    # Set quiet mode as global
    config.quiet = args.quiet

    # If no requested actions, show help
    if not args:
        parser.print_help()
        exit()

main(args)
