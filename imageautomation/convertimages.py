"""
Convert images from one format to another

Classes:


Functions:

    render_pngs_from_cr3s
    correct_sample_png

Variables:

    None

Global Variables (via config):

    config.quiet : bool
        Suppress progress bar output (default False)

"""

# History
#
# 2024-05-10 Add handling for jpeg input files, auto-orient on convert
# 2024-03-29 Handle crop and gravity strings by orientation in render_pngs_from_cr3s
# 2024-03-29 Add -y parameter to ffmpeg command to overwrite existing files
# 2024-03-29 Add long_side parameter to correct_sample_png
# 2024-03-29 Fix render_from_pngs to handle tuplex in cr3_files (filename, long_side)
# 2024-03-19 Add correct_sample_png to apply ffmpeg correction to single PNG
# 2024-03-11 Remove auto-level, normalize, and modulate from initial PNG conversion
# 2024-03-11 Refactor render_pngs_from_cr3s to use run_subprocess
# 2024-03-11 Fix error handling in render_pngs_from_cr3s
# 2024-03-07 Add gravity_string to config
# 2024-03-07 Add crop_string to config
# 2024-03-07 Add modulate_string to config
# 2024-03-06 Add logging and quiet option
# 2024-03-06 Add tqdm progress bar, single-file processing, and working directory
# 2024-03-05 First version

# TODO
# None

#
# Imports
#

# General

# Modules
from .utilities import PrintLog
from .utilities import run_subprocess
from imageautomation.binaries import resolve

# TUI progress bar
from tqdm import tqdm

# Logging
from loguru import logger

# Config for global variables
from imageautomation import runtime as config


def render_pngs_from_cr3s(cr3_files, output_file):
    """
    Render numbered PNGs from RAW (CR3) or JPG inputs.

    RAW inputs are explicitly developed with rawtherapee-cli (neutral
    profile, PNG out) — the same command ImageMagick's dng:decode delegate
    ran implicitly — then ImageMagick applies gravity/crop/resize/orient.
    JPG inputs skip the development step.

    Returns True only if EVERY file in the burst rendered successfully.
    """
    all_ok = True

    for index, (input_file, long_side) in enumerate(
        tqdm(
            cr3_files,
            desc=f"Converting {config.file_extension.upper().replace('.', '')}s to PNGs",
            leave=False,
            disable=True if len(cr3_files) == 1 else config.quiet,
        ),
        start=1,
    ):
        is_jpg = input_file.upper().endswith("JPG")

        # Per-image defaults (user overrides via config win)
        resize_string = "2000" if long_side == "width" else "x2000"
        if config.crop_string:
            im_crop_string = config.crop_string
        elif is_jpg:
            im_crop_string = None
        else:
            im_crop_string = "6000x4000+0+0" if long_side == "width" else "4000x6000+0+0"
        if config.gravity_string:
            im_gravity_string = config.gravity_string
        elif is_jpg:
            im_gravity_string = None
        else:
            im_gravity_string = "SouthEast" if long_side == "width" else "NorthEast"

        # Step 1: develop RAW to PNG (skipped for JPG)
        if is_jpg:
            magick_input = input_file
        else:
            developed = f"{config.working_directory}/{output_file}-develop.png"
            rt_command = [
                resolve("rawtherapee-cli"),
                "-o", developed,
                "-n",
                "-Y",
                "-c", input_file,
            ]
            if not run_subprocess(
                "rawtherapee-cli",
                rt_command,
                f"Developed {input_file}",
                f"Failed to develop {input_file}",
            ):
                all_ok = False
                continue
            magick_input = developed

        # Step 2: gravity/crop/resize/orient with ImageMagick
        command = [resolve("magick"), magick_input]
        if im_gravity_string:
            command += ["-gravity", im_gravity_string]
        if im_crop_string:
            command += ["-crop", im_crop_string]
        command += ["-resize", resize_string, "-auto-orient"]
        command.append(
            f"{config.working_directory}/{output_file}-image_{format(index).zfill(3)}.png"
        )

        if not run_subprocess(
            "magick",
            command,
            f"Converted {input_file} to {output_file}-image_{format(index).zfill(3)}.png",
            f"Failed to convert {input_file}",
        ):
            all_ok = False

    return all_ok


def correct_sample_png(output_file, long_side="width"):
    """
    Apply a correction to a single PNG using ffmpeg with user-requested settings.

    Parameters:

        output_file : str
            The base file name for the input PNG and output PNG files

        long_side : str
            The long side of the image for the resize operation
            (default "width")

    Returns:

        bool
            True if the process was successful, False otherwise
    """
    # Set width or height for resize based on long_side
    if long_side == "width":
        scale_string = "2000:-2"
    else:
        scale_string = "-2:2000"

    # Execute command to apply a correction to the GIF file
    command = [
        resolve("ffmpeg"),
        f"-y",
        f"-i",
        f"{config.working_directory}/{output_file}-image_001.png",
        f"-vf",
        f"scale={scale_string}{config.normalize_string}{config.custom_vf_string}",
        f"{config.destination_path}/{output_file}-testimage.png",
    ]

    result = run_subprocess(
        "ffmpeg",
        command,
        f"Applied correction to {output_file}.png",
        f"Failed to apply correction to {output_file}.png",
    )

    return result
