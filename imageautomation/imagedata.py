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
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

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
        for image_file in tqdm(image_files, desc="Extracting EXIF data", unit="file", disable=config.quiet):
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

    Returns:

        list
            A list of lists, where each list item is a burst and each inner list contains the CR3 files in a burst
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
            }
            output_list.append(burst_info)
        else:
            # Get the CR3 files in the group
            cr3_files = group_df["SourceFile"].tolist()

            # Get the directory of the CR3 files
            cr3_directory = os.path.dirname(cr3_files[0])

            # Concatenate the directory and filename to create the full path filename
            cr3_files = [os.path.join(cr3_directory, filename) for filename in cr3_files]

            # Append the list of full path filenames to the cr3_files_list
            output_list.append(cr3_files)

    PrintLog.debug(f"Detected {len(output_list)} burst(s)")

    return output_list
