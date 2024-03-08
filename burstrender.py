# History
#
# 2024-03-08 V1.3 First deployable-ish version
# 2024-03-07 V1.2 Done with basic image processing CLI and docs
# 2024-03-07 # Update README.md
# 2024-03-07 Add CLI arg for gravity
# 2024-03-07 Add CLI arg for crop string (default 6000x4000+0+0)
# 2024-03-07 Add CLI arg for brightness (default 120)
# 2024-03-07 Document default config.yaml
# 2024-03-07 Add log location to config.yaml
# 2024-03-06 V1.1 Done with basic features
# 2024-03-06 Add basic error handling
# 2024-03-06 Add quiet mode
# 2024-03-06 Add logging
# 2024-03-06 Handle destination of output files based on requests and destination path
# 2024-03-06 Add progress bars
# 2024-03-06 Handle cleaning of working directory
# 2024-03-06 Handle creation of working directory if it does not exist
# 2024-03-06 Add configuration file for working directory
# 2024-03-05 Add command line arguments
# 2024-03-04 V1.0 Initial version

# TODO
# Implement exit codes
# Add CLI arg for movie width (default 2000)
# Add CLI arg for movie speed (default 2.0 / half speed
# Update README.md
# Add validation for modulate, crop, and gravity strings


# FIGURE OUT DEPLOYMENT
# Requirements?  Python 3.11.2, ImageMagick, FFmpeg, ExifTool, set up RawTherapee as helper for ImageMagick ???
# How to install?  pip install -r requirements.txt, sudo apt install imagemagick, sudo apt install ffmpeg, sudo apt install exiftool, sudo apt install rawtherapee ???
# How to add to path? Add to .bashrc ???
# Create a debian package?  https://packaging.ubuntu.com/html/packaging-new-software.html ???


#
# Imports
#

# General
import os
import pathlib
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
from imageautomation.utilities import PrintLog, Configuration

# TUI progress bar
from tqdm import tqdm

# Logging
from loguru import logger

# Config for global variables
import config

# VERSION
version = "1.3"
config.exit_code = 0
config.exir_reason = ""

#
# Set Up Logging
#

# Clear default logger sinks
logger.remove()

# Set log path (and level) from config file
config.log_path = Configuration().get()['logging']['path']
if config.log_path == "default" or not config.log_path:
    config.log_path = f"{pathlib.Path(__file__).parent.absolute() / 'logs'}"
else:
    config.log_path = Configuration().get()['logging']['path']

# TODO: config.log_level = Configuration().get()['logging']['level']

# Add sink for log file
logger.add(
    f"{config.log_path}/burstrender.log",
    rotation="10 MB",
    retention=10,
    backtrace=True,
    diagnose=True,
)

#
# Functions
#


def move_files(target_file, destination_file):
    """
    Move a file to a new location.

    Parameters:

        target_file : str
            The full path filename of the file to be moved

        destination_file : str
            The full path filename of the destination file

    Returns:

        None
    """

    # Execute the mv command to remove files
    try:
        completed_process = subprocess.run(
            [
                f"sh",
                f"-c",
                f"mv {target_file} {destination_file}",
            ],
            capture_output=True,
        )
    # TODO: Logging

    except FileNotFoundError as exc:
        PrintLog.error(
            f"Failed to move {target_file} to {destination_file} "
            f"because the mv executable could not be found\n{exc}"
        )
    except subprocess.CalledProcessError as exc:
        PrintLog.error(
            f"Failed to move {target_file} to {destination_file} "
            f"because mv did not return a successful return code"
            f"Returned {exc.returncode}\n{exc}"
        )

    except subprocess.TimeoutExpired as exc:
        PrintLog.error(
            f"Failed to move {target_file} to {destination_file} "
            f"because process for mv timed out.\n{exc}"
        )

    PrintLog.debug(f"Moved {target_file} to {destination_file}")

def delete_files(filespec):
    """
    Delete a list of files.

    Parameters:

        file_list : list
            A list of full path filenames of the files to be deleted

    Returns:

        None
    """

    # Execute the rm command to remove files
    try:
        completed_process = subprocess.run(
            [
                f"sh",
                f"-c",
                f"rm {filespec}",
            ],
            capture_output=True,
        )

    except FileNotFoundError as exc:
        PrintLog.error(
            f"Failed to remove files {filespec} "
            f"because the executable for rm could not be found\n{exc}"
        )

    except subprocess.CalledProcessError as exc:
        PrintLog.error(
            f"Failed to remove files {filespec} "
            f"because rm did not return a successful return code"
            f"Returned {exc.returncode}\n{exc}"
        )

    except subprocess.TimeoutExpired as exc:
        PrintLog.error(
            f"Failed to remove files {filespec} "
            f"because process for rm timed out.\n{exc}")

    PrintLog.debug(f"Removed files: {filespec}")

def clear_working_directory():
    """
    Clear the working directory of all working files.

    Parameters:

        None

    Returns:

        None
    """

    # Remove all files from the working directory
    if config.working_directory == "":
        PrintLog.error(
            f"Failed to clear working directory because no working directory was set"
        )
        return

    if (
        config.working_directory == "/"
        or config.working_directory == "/home"
        or config.working_directory == "/home/"
    ):
        PrintLog.error(
            f"Working directory is root or home. Will not delete files there!."
        )
        return

    delete_files(f"{config.working_directory}/*.png")
    delete_files(f"{config.working_directory}/*.trf")
    delete_files(f"{config.working_directory}/*.mp4")
    delete_files(f"{config.working_directory}/*.gif")

    PrintLog.debug(f"Cleared working directory: {config.working_directory}")


def cleanup_files(output_file):
    """
    Remove the PNG and TRF files created during the rendering process.

    Parameters:

        output_file : str
            The best filename for the group output (ex. "burst_1")

    Returns:

        None
    """

    # Remove PNG files
    delete_files(f"{config.working_directory}/{output_file}-image_*.png")

    # Remove TRF file
    delete_files(f"{config.working_directory}/{output_file}.trf")


def main(args):
    """
    Main function to render burst photos to MP4s, Stabilized MP4s, and GIFs.
    """
    # Get configuration
    config_yaml = Configuration().get()

    # Set working directory from config file
    config.working_directory = config_yaml["paths"]["working"]
    if config.working_directory == "default":
        config.working_directory = f"{pathlib.Path.home() / '.burstrender' / 'working'}"

    # Assure working directory is valid
    try:
        pathlib.Path(config.working_directory).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        PrintLog.error(
            f"Could not create working directory: {config.working_directory}. "
            f"Assure you have permissions or change the working directory in config.yaml"
        )
        exit()

    PrintLog.debug(f"Working directory confirmed/created: {config.working_directory}")

    # Empty the working directory
    clear_working_directory()

    #
    # Set global variables
    #

    # Set the source path for the input CR3 files
    if args.source_path:
        config.source_path = args.source_path
        PrintLog.debug(f"Source path from CLI arg: {config.source_path}")
    else:
        config.source_path = "."
        PrintLog.debug(f"Default source path: {config.source_path}")

    # Set the destination path for the rendered videos and/or gifs
    if args.destination_path:
        config.destination_path = args.destination_path
        PrintLog.debug(f"Destination path from CLI arg: {config.destination_path}")
    else:
        config.destination_path = os.getcwd()
        PrintLog.debug(f"Default destination path: {config.destination_path}")

    # Set the minimum time between detected bursts in seconds
    if args.seconds_between_bursts:
        config.seconds_between_bursts = args.seconds_between_bursts
        PrintLog.debug(f"Seconds between bursts from CLI arg: {config.seconds_between_bursts}")
    else:
        config.seconds_between_bursts = 2
        PrintLog.debug(f"Default seconds between bursts: {config.seconds_between_bursts}")

    # Set the minimum number of photos in burst
    if args.minimum_burst_length:
        config.min_burst_length = args.minimum_burst_length
        PrintLog.debug(f"Minimum burst length from CLI arg: {config.min_burst_length}")
    else:
        config.min_burst_length = 10
        PrintLog.debug(f"Default minimum burst length: {config.min_burst_length}")

    # Set the modulate string for ImageMagick
    if args.modulate_string:
        config.modulate_string = args.modulate_string
        PrintLog.debug(f"Modulate string from CLI arg: {config.modulate_string}")
    else:
        config.modulate_string = "120"
        PrintLog.debug(f"Default modulate string: {config.modulate_string}")

    # Set the crop string for ImageMagick
    if args.crop_string:
        config.crop_string = args.crop_string
        PrintLog.debug(f"Crop string from CLI arg: {config.crop_string}")
    else:
        config.crop_string = "6000x4000+0+0"
        PrintLog.debug(f"Default crop string: {config.crop_string}")

    # Set the gravity string for ImageMagick
    if args.gravity_string:
        config.gravity_string = args.gravity_string
        PrintLog.debug(f"Gravity string from CLI arg: {config.gravity_string}")
    else:
        config.gravity_string = "SouthEast"
        PrintLog.debug(f"Default gravity string: {config.gravity_string}")

    #
    # Process images
    #

    # Call the extractEXIF function to extract EXIF data from the images
    df = extractEXIF(config.source_path)

    # Exit if no CR3 files are found
    if df.empty:
        PrintLog.warning(
            f"No CR3 files found in the source path: {config.source_path}/ "
            f"Use the --source-path argument to specify a different source path"
        )
        exit()

    # Call the detect_bursts function to detect burst photo groups
    if args.detect_only:
        burst_info = detect_bursts(df, True, config.seconds_between_bursts, config.min_burst_length)

        PrintLog.debug(f"Output data for --detect-only")
        
        print(f"Detected {len(burst_info)} burst(s):")
        for burst in burst_info:
            print(
                f"  Burst {burst_info.index(burst) + 1}: {burst['start']} to {burst['end']} ({burst['frames']} photos)"
            )
        exit()
    else:
        cr3_files_list = detect_bursts(
            df, False, config.seconds_between_bursts, config.min_burst_length
        )

    # Output sample images and exit if requested
    if args.sample_images_only:

        # Iterate over each group of CR3 files and output the first image of each burst
        for cr3_files in tqdm(
            cr3_files_list, desc="Rendering PNGs", unit="burst", disable=config.quiet
        ):
            # Get the output file path for the PNG
            output_file = "burst_{}".format(cr3_files_list.index(cr3_files) + 1)

            # Render PNGs from CR3 files
            if not render_pngs_from_cr3s([cr3_files[0]], output_file):
                continue

        # Done
        exit()

    #
    # Process bursts
    #

    # Iterate over each group of CR3 files
    for cr3_files in tqdm(
        cr3_files_list, desc="Processing Bursts", unit="burst", disable=config.quiet
    ):
        PrintLog.debug("Processing burst {}".format(cr3_files_list.index(cr3_files) + 1))

        # Get the output file path for the GIF
        output_file = "burst_{}".format(cr3_files_list.index(cr3_files) + 1)

        # Render PNGs from CR3 files
        if not render_pngs_from_cr3s(cr3_files, output_file):
            PrintLog.error(f"Failed to render PNGs from CR3 files for {output_file}")
            cleanup_files(output_file)
            continue

        # Set rendering progress bar
        if args.no_stabilization:
            render_action_count = 4
        else:
            render_action_count = 5

        # Set rendering progress bar
        render_progress_bar = tqdm(
            total=render_action_count,
            desc="Rendering MP4",
            unit="action",
            leave=False,
            disable=config.quiet,
        )

        # Create MP4 from PNGs
        if not create_mp4(output_file):
            PrintLog.error(f"Failed to create MP4 from PNGs for {output_file}")
            cleanup_files(output_file)
            exit()

        PrintLog.debug(f"Created MP4 from PNGs for {output_file}")
        render_progress_bar.update(1)
        render_progress_bar.refresh()


        # Stabilize MP4
        if not args.no_stabilization:
            render_progress_bar.set_description("Stabilizing MP4")
            render_progress_bar.refresh()

            if not stabilize_mp4(output_file):
                PrintLog.error(f"Failed to stabilize MP4 for {output_file}")
                cleanup_files(output_file)
                exit()

            PrintLog.debug(f"Stabilized MP4 for {output_file}") 
            render_progress_bar.update(1)
            render_progress_bar.refresh()

        # Create GIF from MP4
        render_progress_bar.set_description("Creating GIF")
        render_progress_bar.refresh()

        if not create_gif_from_mp4(output_file, args.no_stabilization):
            PrintLog.error(f"Failed to create GIF from MP4 for {output_file}")
            cleanup_files(output_file)
            exit()

        PrintLog.debug(f"Created GIF from MP4 for {output_file}")
        render_progress_bar.update(1)
        render_progress_bar.refresh()

        # Move output files to destination path
        render_progress_bar.set_description("Moving Output Files")
        render_progress_bar.refresh()

        if not args.gif_only:
            move_files(
                f"{config.working_directory}/{output_file}.mp4",
                f"{config.destination_path}/{output_file}.mp4",
            )

        if not args.no_stabilization and not args.gif_only:
            move_files(
                f"{config.working_directory}/{output_file}-stabilized.mp4",
                f"{config.destination_path}/{output_file}-stabilized.mp4",
            )

        move_files(
            f"{config.working_directory}/{output_file}.gif",
            f"{config.destination_path}/{output_file}.gif",
        )

        render_progress_bar.update(1)
        render_progress_bar.refresh()

        # Cleanup files
        render_progress_bar.set_description("Cleaning Up Temp Files")
        render_progress_bar.refresh()

        cleanup_files(output_file)

        render_progress_bar.update(1)
        render_progress_bar.refresh()
        
        # Close render progress bar
        render_progress_bar.close()

        PrintLog.success("Completed burst {}".format(cr3_files_list.index(cr3_files) + 1))


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
        "--no-stabilization",
        action="store_true",
        help="Do not stabilize the images",
    )

    parser.add_argument(
        "--gif-only",
        action="store_true",
        help="Keep only final GIF and remove prelim MP4 files",
    )

    parser.add_argument(
        "--modulate-string",
        action="store",
        help="Specify a modulate string for ImageMagick. (Default is 120.)",
    )

    parser.add_argument(
        "--crop-string",
        action="store",
        help="Specify a crop string for ImageMagick. (Default is 6000x4000+0+0.)",
    )

    parser.add_argument(
        "--gravity-string",
        action="store",
        help="Specify a gravity string for ImageMagick. (Default is SouthEast.)",
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
