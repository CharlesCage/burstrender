"""
Manage image data

Classes:


Functions:

    extractEXIF
    detect_bursts

Variables:

    None

Global Variables (via config):

    config.quiet : bool
        Suppress progress bar output (default False)

"""

# History
#
# 2024-05-10 Add handling for jpeg input files
# 2024-03-29 Add long side detection to detect_bursts
# 2024-03-11 Update documentation
# 2024-03-06 Add logging and quiet option
# 2024-03-05 Added detect-only functionality and tqdm progress bar
# 2024-03-05 Initial version

# TODO
# None

#
# Imports
#

# General
import os
import pandas as pd
import warnings
import exiftool

# Modules
from .utilities import PrintLog

# TUI progress bar
from tqdm import tqdm

# Logging
from loguru import logger

# Config for global variables
import config

# Ignore pandas warnings
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)


def extractEXIF(directory, file_extension=".cr3"):
    """
    Extract EXIF data from specifiedx files in a directory and return as a pandas dataframe.

    Parameters:

        directory : str
            The directory containing the CR3 files
        file_extension : str
            The file extension of the desired files (default ".cr3")

    Returns:

        df : pandas.DataFrame
            A pandas dataframe containing the EXIF data from the CR3 files

    """

    # Create an instance of the ExifTool class
    with exiftool.ExifTool() as et:
        # Get a list of all image files in the directory
        image_files = [
            file
            for file in os.listdir(directory)
            if file.lower().endswith((file_extension))
        ]

        # Create an empty pandas dataframe to store the EXIF data
        df = pd.DataFrame()

        # Iterate over each image file
        for image_file in tqdm(
            image_files, desc="Extracting EXIF data", unit="file", disable=config.quiet
        ):
            # Get the full path of the image file
            image_path = os.path.join(directory, image_file)

            # Extract the EXIF data using ExifTool
            exif_data = et.get_metadata(image_path)

            # Append the EXIF data to the dataframe
            df = pd.concat([df, pd.DataFrame([exif_data])], ignore_index=True)

    PrintLog.debug(f"Extracted EXIF data from {len(df)} CR3 files")

    # Return the Da the dataframe
    return df


def detect_bursts(df, detect_only=False, seconds_between_bursts=2, min_burst_length=10):
    """
    Detect burst photos in a dataframe based on the time difference between consecutive rows.

    Parameters:

        df : pandas.DataFrame
            A pandas dataframe containing the EXIF data from the CR3 files

        detect_only : bool
            If True, return a list of burst_info dictionaries instead of a list of CR3 files (default False)

        seconds_between_bursts : int
            The maximum time difference in seconds between consecutive rows to consider as a burst (default 2)

        min_burst_length : int
            The minimum number of CR3 files in a burst to be considered a burst (default 10)

    Returns:

        output_list : list of tuples
            A list of tuples (path/filename and long_side) for CR3 files in each burst
            or a list of burst_info dictionaries if detect_only is True
    """

    # Combine the columns EXIF:DateTimeOriginal and EXIF:SubSecTimeOriginal into a new column
    df["Timestamp"] = df.apply(
        lambda row: pd.to_datetime(
            row["EXIF:DateTimeOriginal"] + "." + str(row["EXIF:SubSecTimeOriginal"]),
            format="%Y:%m:%d %H:%M:%S.%f",
        ),
        axis=1,
    )

    # Combine the columns EXIF:DateTimeOriginal and EXIF:SubSecTimeOriginal into a new column
    df["LongSide"] = df.apply(
        lambda row: "width" if row["EXIF:Orientation"] == 1 else "height", axis=1
    )

    # Sort the dataframe by the 'Timestamp' column in increasing order
    df = df.sort_values("Timestamp", ascending=True)

    # Calculate the time difference between consecutive rows
    df["TimeDiff"] = df["Timestamp"].diff()

    # Create a mask to identify rows where the time difference is greater than or equal to 2 seconds
    mask = df["TimeDiff"] >= pd.Timedelta(seconds=seconds_between_bursts)

    # Assign a group number to each row based on the mask
    df["Group"] = mask.cumsum()

    # Group the dataframe by the 'Group' column
    groups = df.groupby("Group")

    # Empty list to store the CR3 files in each group
    output_list = []

    # Iterate over each group
    for group, group_df in groups:

        # If the group contains only one CR3 file, skip it
        if len(group_df) < min_burst_length:
            continue

        # If detect_only is True, add the number of frames in the burst and the start and end times to the burst_info list
        if detect_only:
            burst_info = {
                "frames": len(group_df),
                "start": group_df["Timestamp"].iloc[0],
                "end": group_df["Timestamp"].iloc[-1],
                "long_side": group_df["LongSide"].iloc[0],
            }
            output_list.append(burst_info)
        else:
            # Get the CR3 files in the group
            cr3_files = group_df["SourceFile"].tolist()

            # Get the long side of the files in the group
            cr3_long_side = group_df["LongSide"].tolist()

            # Get the directory of the CR3 files
            cr3_directory = os.path.dirname(cr3_files[0])

            # Concatenate the directory and filename to create the full path filename
            cr3_files = [
                os.path.join(cr3_directory, filename) for filename in cr3_files
            ]

            # Combine the CR3 files and long side into a list of tuples
            cr3_list = list(zip(cr3_files, cr3_long_side))

            # Append the list of full path filenames to the cr3_files_list
            output_list.append(cr3_list)

    PrintLog.debug(f"Detected {len(output_list)} burst(s)")

    return output_list
