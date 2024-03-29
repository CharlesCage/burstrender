# History
#
# 2024-03-29 Update README.md to document new features, increment version to 3.0
# 2024-03-29 Handle portrait mode
# 2024-03-29 Fix issue with files existing in move files
# 2024-03-29 Add long side detection to detect_bursts
# 2024-03-29 Adjust code to handle individual image crop/gravity strings
# 2024-03-19 # Update README.md to document new featuresw
# 2024-03-19 Increment version to 2.1
# 2024-03-19 Adjust sample PNG correction to use ffmpeg
# 2024-03-19 Increment version to 2.0
# 2024-03-19 Add CLI arg for custom -vf string
# 2024-03-19 Remove CLI arg for modulate string
# 2024-03-19 Add CLI arg for disabling ffmpeg normalization
# 2024-03-19 Add default ffmpeg normalization
# 2024-03-19 Remove final ImageMagick pass
# 2024-03-18 Move correction to final ImageMagick pass
# 2024-03-18 Increment version to 1.5
# 2024-03-18 Add -normalize beforre -auto-level
# 2024-03-11 Validate minimum burst length
# 2024-03-11 Validate seconds between bursts
# 2024-03-11 Validate gravity string
# 2024-03-11 v1.4 Exit code
# 2024-03-11 Update README.md
# 2024-03-11 Implement exit codes
# 2024-03-11 Refactor to use run_subprocess, clean up imports
# 2024-03-11 Convert source/dest paths to absolute
# 2024-03-11 Implement quiet mode
# 2024-03-11 Add logging level selection
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
# Fix quote issue in move_files
# Add recursive folder search for CR3 files
# Detect and handle portrait mode

# Add CLI arg for movie speed (default 2.0 / half speed

#
# Imports
#

# General
import os
import sys
import pathlib
import argparse

# Modules
from imageautomation.imagedata import extractEXIF
from imageautomation.imagedata import detect_bursts
from imageautomation.combineimages import create_mp4
from imageautomation.combineimages import stabilize_mp4
from imageautomation.combineimages import create_gif_from_mp4
from imageautomation.convertimages import render_pngs_from_cr3s
from imageautomation.convertimages import correct_sample_png
from imageautomation.utilities import PrintLog, Configuration, run_subprocess

# TUI progress bar
from tqdm import tqdm

# Logging
from loguru import logger

# Config for global variables
import config

# VERSION
version = "3.0"
config.exit_code = 0
config.exir_reason = ""

#
# Set Up Logging
#

# Clear default logger sinks
logger.remove()

# Set log path (and level) from config file
config.log_path = Configuration().get()["logging"]["path"]
if config.log_path == "default" or not config.log_path:
    config.log_path = f"{pathlib.Path(__file__).parent.absolute() / 'logs'}"
else:
    config.log_path = Configuration().get()["logging"]["path"]

config.log_level = Configuration().get()["logging"]["level"].upper()
if config.log_level == "DEFAULT" or not config.log_level:
    config.log_level = "DEBUG"
elif not any(
    config.log_level in s
    for s in ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
):
    config.log_level = "DEBUG"

# Add sink for log file
logger.add(
    f"{config.log_path}/burstrender.log",
    level=config.log_level,
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

        result : bool
            True if the process was successful, False otherwise
    """

    # Execute the mv command to remove files
    command = [
        f"sh",
        f"-c",
        f"mv {target_file} {destination_file}",
    ]

    result = run_subprocess(
        "mv",
        command,
        f"Moved {target_file} to {destination_file}",
        f"Failed to move {target_file} to {destination_file}",
    )

    return result


def delete_files(filespec):
    """
    Delete a list of files.

    Parameters:

        file_list : list
            A list of full path filenames of the files to be deleted

    Returns:

        result : bool
            True if the process was successful, False otherwise
    """

    # Execute the rm command to remove files

    # protection here to assure that filespec is not a directory or root
    if filespec == "/" or filespec == "/home" or filespec == "/home/":
        PrintLog.error(
            f"Will not delete files in root or home. Will not delete files: {filespec}"
        )
        return False

    command = [
        f"sh",
        f"-c",
        f"rm {filespec}",
    ]

    result = run_subprocess(
        "rm",
        command,
        f"Removed files: {filespec}",
        f"Failed to remove files: {filespec}",
    )

    return result


def clear_working_directory():
    """
    Clear the working directory of all working files.

    Parameters:

        None (uses global variable config.working_directory)

    Returns:

        result : bool
            True if the process was successful, False otherwise
    """

    # Remove all files from the working directory
    if config.working_directory == "":
        PrintLog.error(
            f"Failed to clear working directory because no working directory was set"
        )
        return False

    if (
        config.working_directory == "/"
        or config.working_directory == "/home"
        or config.working_directory == "/home/"
    ):
        PrintLog.error(
            f"Working directory is root or home. Will not delete files there!."
        )
        return False

    result = True

    if not delete_files(f"{config.working_directory}/*.png"):
        result = False

    if not delete_files(f"{config.working_directory}/*.trf"):
        result = False

    if not delete_files(f"{config.working_directory}/*.mp4"):
        result = False

    if not delete_files(f"{config.working_directory}/*.gif"):
        result = False

    if not result:
        PrintLog.warning(
            f"Failed to clear working directory: {config.working_directory}"
        )
        return False
    else:
        PrintLog.debug(f"Cleared working directory: {config.working_directory}")
        return True


def cleanup_files(output_file):
    """
    Remove the PNG and TRF files created during the rendering process.

    Parameters:

        output_file : str
            The best filename for the group output (ex. "burst_1")

        Uses global variable config.working_directory

    Returns:

        result : bool
            True if the process was successful, False otherwise
    """

    result = True

    # Remove PNG files
    if not delete_files(f"{config.working_directory}/{output_file}-image_*.png"):
        result = False

    # Remove TRF file
    if not delete_files(f"{config.working_directory}/{output_file}.trf"):
        result = False

    return result


def move_output_files(output_file, mp4=True, stabilized=True, gif=True):
    """
    Move the output files to the destination path.

    Parameters:

        output_file : str
            The best filename for the group output (ex. "burst_1")

        mp4 : bool
            Move the MP4 file if True

        stabilized : bool
            Move the stabilized MP4 file if True

        gif : bool
            Move the GIF file if True

        Uses global variables config.working_directory and config.destination_path

    Returns:

        result : bool
            True if the process was successful, False otherwise
    """

    result = True

    # Move MP4 file
    if mp4:
        if not move_files(
            f"{config.working_directory}/{output_file}.mp4",
            f"{config.destination_path}/{output_file}.mp4",
        ):
            result = False

    # Move stabilized MP4 file
    if stabilized:
        if not move_files(
            f"{config.working_directory}/{output_file}-stabilized.mp4",
            f"{config.destination_path}/{output_file}-stabilized.mp4",
        ):
            result = False

    # Move GIF file
    if gif:
        if not move_files(
            f"{config.working_directory}/{output_file}.gif",
            f"{config.destination_path}/{output_file}.gif",
        ):
            result = False

    return result


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
        PrintLog.critical(
            f"Could not create or access working directory: {config.working_directory}. "
            f"Assure you have permissions or change the working directory in config.yaml"
        )
        sys.exit(config.exit_code)

    PrintLog.debug(f"Working directory confirmed/created: {config.working_directory}")

    # Empty the working directory
    if not clear_working_directory():
        PrintLog.warning(f"Failed to clear the working directory")
    else:
        PrintLog.debug(f"Cleaned up the working directory")

    #
    # Set global variables
    #

    # Set the source path for the input CR3 files
    if args.source_path:
        config.source_path = os.path.abspath(args.source_path)
        PrintLog.debug(f"Source path from CLI arg: {config.source_path}")
    else:
        config.source_path = "."
        PrintLog.debug(f"Default source path: {config.source_path}")

    # Set the destination path for the rendered videos and/or gifs
    if args.destination_path:
        config.destination_path = os.path.abspath(args.destination_path)
        PrintLog.debug(f"Destination path from CLI arg: {config.destination_path}")
    else:
        config.destination_path = os.getcwd()
        PrintLog.debug(f"Default destination path: {config.destination_path}")

    # Set the minimum time between detected bursts in seconds
    if args.seconds_between_bursts:
        config.seconds_between_bursts = args.seconds_between_bursts

        # Validate seconds between bursts (positive integer)
        try:
            config.seconds_between_bursts = int(config.seconds_between_bursts)
            if config.seconds_between_bursts < 1:
                PrintLog.critical(
                    f"Invalid seconds between bursts: {config.seconds_between_bursts}. Must be a positive integer."
                )
                sys.exit(config.exit_code)
        except ValueError:
            PrintLog.critical(
                f"Invalid seconds between bursts: {config.seconds_between_bursts}. Must be a positive integer."
            )
            sys.exit(config.exit_code)

        PrintLog.debug(
            f"Seconds between bursts from CLI arg: {config.seconds_between_bursts}"
        )
    else:
        config.seconds_between_bursts = 2
        PrintLog.debug(
            f"Default seconds between bursts: {config.seconds_between_bursts}"
        )

    # Set the minimum number of photos in burst
    if args.minimum_burst_length:
        config.min_burst_length = args.minimum_burst_length

        # Validate minimum burst length (positive integer)
        try:
            config.min_burst_length = int(config.min_burst_length)
            if config.min_burst_length < 1:
                PrintLog.critical(
                    f"Invalid minimum burst length: {config.min_burst_length}. Must be a positive integer."
                )
                sys.exit(config.exit_code)
        except ValueError:
            PrintLog.critical(
                f"Invalid minimum burst length: {config.min_burst_length}. Must be a positive integer."
            )
            sys.exit(config.exit_code)

        PrintLog.debug(f"Minimum burst length from CLI arg: {config.min_burst_length}")
    else:
        config.min_burst_length = 10
        PrintLog.debug(f"Default minimum burst length: {config.min_burst_length}")

    # Set the normalizattion string for ffmpeg based on CLI arg
    if args.no_normalize:
        config.normalize_string = ""
        PrintLog.debug(f"Normalization disabled from CLI arg")
    else:
        config.normalize_string = ",normalize=blackpt=black:whitept=white:smoothing=50"
        PrintLog.debug(f"Default normalization string: {config.normalize_string}")

    # Set the custom -vf string for ffmpeg based on CLI arg
    if args.custom_vf_string:
        config.custom_vf_string = f",{args.custom_vf_string}"
        PrintLog.debug(f"Custom -vf string from CLI arg: {config.custom_vf_string}")
    else:
        config.custom_vf_string = ""

    # Set the crop string for ImageMagick
    if args.crop_string:
        config.crop_string = args.crop_string
        PrintLog.debug(f"Crop string from CLI arg: {config.crop_string}")
    else:
        config.crop_string = None
        PrintLog.debug(f"Default crop string: 6000x4000+0+0 or 4000x6000+0+0 based on orientation")

    # Set the gravity string for ImageMagick
    if args.gravity_string:
        config.gravity_string = args.gravity_string

        # Validate gravity string
        if config.gravity_string not in [
            "NorthWest",
            "North",
            "NorthEast",
            "West",
            "Center",
            "East",
            "SouthWest",
            "South",
            "SouthEast",
        ]:
            PrintLog.critical(
                f"Invalid gravity string: {config.gravity_string}. "
                f"Must be one of: NorthWest, North, NorthEast, West, Center, East, SouthWest, South, SouthEast"
            )
            sys.exit(config.exit_code)
        PrintLog.debug(f"Gravity string from CLI arg: {config.gravity_string}")
    else:
        config.gravity_string = None
        PrintLog.debug(f"Default gravity string: SouthEast or NorthEast based on orientation")

    # Set the quiet mode
    config.quiet = args.quiet

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
        sys.exit(config.exit_code)

    # Call the detect_bursts function to detect burst photo groups
    if args.detect_only:
        burst_info = detect_bursts(
            df,
            True,
            config.seconds_between_bursts,
            config.min_burst_length,
        )

        PrintLog.debug(f"Output data for --detect-only")

        print(f"Detected {len(burst_info)} burst(s):")
        for burst in burst_info:
            print(
                f"  Burst {burst_info.index(burst) + 1}: "
                f"{burst['start']} to {burst['end']} ({burst['frames']} photos, "
                 f"{'landscape' if burst['long_side'] == 'width' else 'portrait'})"
            )
        sys, exit(config.exit_code)
    else:
        cr3_files_list = detect_bursts(
            df,
            False,
            config.seconds_between_bursts,
            config.min_burst_length,
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
            
            # Apply correction to PNG and move to destination path
            if not correct_sample_png(output_file, cr3_files[0][1]):
                PrintLog.warning(f"Failed to correct sample PNG for {output_file}")
                continue

        # Clean up working directory
        if not clear_working_directory():
            PrintLog.warning(f"Failed to clear the working directory")
        else:
            PrintLog.debug(f"Cleaned up the working directory")

        # Done
        sys.exit(config.exit_code)

    #
    # Process bursts
    #

    # Set output values
    output_gif = True
    if args.gif_only:
        output_mp4 = False
        output_stabilized = False
    else:
        output_mp4 = True
        output_stabilized = not args.no_stabilization

    # Iterate over each group of CR3 files
    for cr3_files in tqdm(
        cr3_files_list, desc="Processing Bursts", unit="burst", disable=config.quiet
    ):
        PrintLog.debug(
            "Processing burst {}".format(cr3_files_list.index(cr3_files) + 1)
        )

        # Get the output file path for the GIF
        output_file = "burst_{}".format(cr3_files_list.index(cr3_files) + 1)

        # Render PNGs from CR3 files
        if not render_pngs_from_cr3s(cr3_files, output_file):
            PrintLog.info(
                f"Failed to render some PNGs from CR3 files for {output_file}. Skipping."
            )
            if not cleanup_files(output_file):
                PrintLog.warning(f"Failed to cleanup files for {output_file}")
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
        if not create_mp4(output_file, cr3_files_list[0][0][1]):
            PrintLog.error(
                f"Failed to create MP4 from PNGs for {output_file}. Skipping."
            )
            if not cleanup_files(output_file):
                PrintLog.warning(f"Failed to cleanup files for {output_file}")
            continue

        PrintLog.debug(f"Created MP4 from PNGs for {output_file}")
        render_progress_bar.update(1)
        render_progress_bar.refresh()

        # Stabilize MP4
        if not args.no_stabilization:
            render_progress_bar.set_description("Stabilizing MP4")
            render_progress_bar.refresh()

            if not stabilize_mp4(output_file):
                PrintLog.error(f"Failed to stabilize MP4 for {output_file}. Skipping.")
                if not move_output_files(output_file, output_mp4, False, False):
                    PrintLog.warning(f"Failed to move files for {output_file}")
                if not cleanup_files(output_file):
                    PrintLog.warning(f"Failed to cleanup files for {output_file}")
                continue

            PrintLog.debug(f"Stabilized MP4 for {output_file}")
            render_progress_bar.update(1)
            render_progress_bar.refresh()

        # Create GIF from MP4
        render_progress_bar.set_description("Creating GIF")
        render_progress_bar.refresh()

        if not create_gif_from_mp4(output_file, cr3_files_list[0][0][1], args.no_stabilization):
            PrintLog.error(
                f"Failed to create GIF from MP4 for {output_file}. Skipping."
            )
            if not move_output_files(output_file, output_mp4, output_stabilized, False):
                PrintLog.warning(f"Failed to move files for {output_file}")
            if not cleanup_files(output_file):
                PrintLog.warning(f"Failed to cleanup files for {output_file}")
            continue

        PrintLog.debug(f"Created GIF from MP4 for {output_file}")
        render_progress_bar.update(1)
        render_progress_bar.refresh()

        # Move output files to destination path
        render_progress_bar.set_description("Moving Output Files")
        render_progress_bar.refresh()

        if not move_output_files(
            output_file, output_mp4, output_stabilized, output_gif
        ):
            PrintLog.warning(f"Failed to move files for {output_file}")

        render_progress_bar.update(1)
        render_progress_bar.refresh()

        # Cleanup files
        render_progress_bar.set_description("Cleaning Up Temp Files")
        render_progress_bar.refresh()

        if not cleanup_files(output_file):
            PrintLog.warning(f"Failed to cleanup files for {output_file}")

        render_progress_bar.update(1)
        render_progress_bar.refresh()

        # Close render progress bar
        render_progress_bar.close()

        PrintLog.success(
            "Completed burst {}".format(cr3_files_list.index(cr3_files) + 1)
        )

    # Done
    sys.exit(config.exit_code)


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
        help="Render the PNG for first image of each burst only, apply any ffmpeg corrections, and move to destination path",
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
        "--no-normalize",
        action="store_true",
        help="Disable automatic normalization of the MP4 files via ffmpeg",
    )
    parser.add_argument(
        "--custom-vf-string",
        action="store",
        help="Specify a custom -vf string for ffmpeg. (Will come after scaling, speed, and normalization if not disabled. A preceding comma is not required.)",
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
