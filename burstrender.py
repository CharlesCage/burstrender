# History
#
# 1.0 - 2024-03-04 - Initial version

# TODO
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
import exiftool
import subprocess
import argparse

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

def extractEXIF(directory):
    """
    Extract EXIF data from CR3 files in a directory and return as a pandas dataframe.

    Parameters:

        directory : str
            The directory containing the CR3 files

    Returns:

        df : pandas.DataFrame
            A pandas dataframe containing the EXIF data from the CR3 files

    """

    # Create an instance of the ExifTool class
    with exiftool.ExifTool() as et:
        # Get a list of all image files in the directory
        image_files = [
            file for file in os.listdir(directory) if file.lower().endswith((".cr3"))
        ]

        # Create an empty pandas dataframe to store the EXIF data
        df = pd.DataFrame()

        # Iterate over each image file
        for image_file in image_files:
            # Get the full path of the image file
            image_path = os.path.join(directory, image_file)

            # Extract the EXIF data using ExifTool
            exif_data = et.get_metadata(image_path)

            # Append the EXIF data to the dataframe
            df = pd.concat([df, pd.DataFrame([exif_data])], ignore_index=True)

    # Return the Da the dataframe
    return df


def render_pngs(cr3_files, output_file):
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
    for cr3_file in cr3_files:
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
                    f"{output_file}-image_{format(cr3_files.index(cr3_file) + 1).zfill(3)}.png",
                ],
                capture_output=True,
            )
            # Print "File X of X converted" if the process was successful
            print(f"File {cr3_files.index(cr3_file) + 1} of {len(cr3_files)} converted")
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


def cleanup_files(output_file):
    """
    Remove the PNG and TRF files created during the rendering process.

    Parameters:

        output_file : str
            The output file name for the PNG files

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

def detect_bursts(df):
    """
    Detect burst photos in a dataframe based on the time difference between consecutive rows.

    Parameters:

        df : pandas.DataFrame
            A pandas dataframe containing the EXIF data from the CR3 files

    Returns:

        list
            A list of lists, where each inner list contains the CR3 files in a burst
    """

    # Combine the columns EXIF:DateTimeOriginal and EXIF:SubSecTimeOriginal into a new column
    df["Timestamp"] = df.apply(
        lambda row: pd.to_datetime(
            row["EXIF:DateTimeOriginal"] + "." + str(row["EXIF:SubSecTimeOriginal"]),
            format="%Y:%m:%d %H:%M:%S.%f",
        ),
        axis=1,
    )

    # Sort the dataframe by the 'Timestamp' column in increasing order
    df = df.sort_values("Timestamp", ascending=True)

    # Calculate the time difference between consecutive rows
    df["TimeDiff"] = df["Timestamp"].diff()

    # Create a mask to identify rows where the time difference is greater than or equal to 2 seconds
    mask = df["TimeDiff"] >= pd.Timedelta(seconds=2)

    # Assign a group number to each row based on the mask
    df["Group"] = mask.cumsum()

    # Group the dataframe by the 'Group' column
    groups = df.groupby("Group")

    # Empty list to store the CR3 files in each group
    cr3_files_list = []

    # Iterate over each group
    for group, group_df in groups:
        # Get the CR3 files in the group
        cr3_files = group_df["SourceFile"].tolist()

        # Get the directory of the CR3 files
        cr3_directory = os.path.dirname(cr3_files[0])

        # Concatenate the directory and filename to create the full path filename
        cr3_files = [os.path.join(cr3_directory, filename) for filename in cr3_files]

        # Append the list of full path filenames to the cr3_files_list
        cr3_files_list.append(cr3_files)

    return cr3_files_list
def main(args):
    """
    Main function to render burst photos to MP4s, Stabilized MP4s, and GIFs.
    """

    # Call the extractEXIF function to extract EXIF data from the images
    df = extractEXIF(
        "/home/chuckcage/Insync/chuckcage@corporation3355.org/Google Drive/SportsPhotos/Burst Photos"
    )

    # Call the detect_bursts function to detect burst photo groups
    cr3_files_list = detect_bursts(df)

    print(f"Detected {len(cr3_files_list)} burst(s)")

    # Iterate over each group of CR3 files
    for cr3_files in cr3_files_list:
        # Get the output file path for the GIF
        output_file = "burst_{}".format(cr3_files_list.index(cr3_files) + 1)

        # Render PNGs from CR3 files
        if not render_pngs(cr3_files, output_file):
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
        "-d",
        "--detect-only",
        action="store_true",
        help="Detect burst photos and display information only",
    )

    parser.add_argument(
        "-s",
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
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + version,
        help="Show program version",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress bars",
    )

    args = parser.parse_args()

    # Set quiet mode as global
    config.quiet = args.quiet

    # If no requested actions, show help
    if not args:
        parser.print_help()
        exit()

main(args)
