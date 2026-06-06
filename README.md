# BurstRender

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

BurstRender looks at a folder full of photos (CR3 RAW from a Canon R3, or JPGs), figures out which ones belong to the same burst, and turns each burst into an MP4 movie, a shake-stabilized MP4, and a looping GIF. I originally threw it together for a friend who photographs his daughter's softball team and wanted an easy way to turn the thousands of photos he shoots at each game into parent- and player-friendly movies and GIFs.

It started out kinda hacky. As of v5, it's considerably less hacky.

## What's New in v5

The original version only ran on Linux (or WSL under Windows), needed four separately-installed tools to work, and — as my friend discovered — quietly fell apart as system updates rolled by underneath it. v5 fixes all of that:

* **A real Windows app.** One zip file with *everything* inside — Python, exiftool, ffmpeg, ImageMagick, and RawTherapee are all bundled. No WSL, no Linux, no installing anything else, and nothing for Windows Update to break. Ever.
* **A guided GUI.** `burstrender-gui.exe` walks you through the whole detect → preview → render workflow with folder pickers, knobs, preview images, and progress bars. No terminal required.
* **The same CLI you know.** Every flag from previous versions still works, on both Windows and Linux.
* **`--doctor`.** One command that tells you whether all the tools BurstRender depends on are present and working. If something's wrong, this is the first thing to run.
* **A pile of bug fixes**, including one where a portrait burst following a landscape burst rendered with the wrong dimensions, and proper handling of filenames with spaces and quotes.
* **Releases are built and tested automatically.** Every release zip gets smoke-tested on a clean Windows machine before it's published — it rendered a real burst all the way to a GIF before you ever downloaded it.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Using the GUI](#using-the-gui)
- [Using the CLI](#using-the-cli)
- [Troubleshooting](#troubleshooting)
- [TODO](#todo)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

**Windows, no terminal (most people):** [Download the latest release](https://github.com/CharlesCage/burstrender/releases/latest), extract the zip anywhere, double-click `burstrender-gui.exe`, and follow the three tabs. That's the whole thing.

**Windows, terminal:** same download, then run `burstrender.exe` from a terminal in the extracted folder — same flags as the Linux CLI below.

**Linux:** install the four tools with apt, clone the repo, make a venv. Details below.

## Installation

### Windows (recommended)

1. Download `burstrender-windows-x64.zip` from the [latest release](https://github.com/CharlesCage/burstrender/releases/latest). It's about 300MB because everything BurstRender needs is inside it.
2. Right-click → **Extract All** → put it anywhere you like (e.g. `C:\burstrender`).
3. Open the folder and run **`burstrender-gui.exe`** for the guided window, or `burstrender.exe` from a terminal for the classic CLI.

**First run:** Windows SmartScreen will show a blue "Windows protected your PC" warning, because the app isn't code-signed (code-signing certificates cost real money and this is a free tool for shooting softball games). Click **More info → Run anyway**. You'll only see it once.

**Updating:** delete the folder, download the new zip, extract. That's the entire update procedure — nothing is installed anywhere else on your system, no registry entries, nothing.

**Why this can't rot:** every tool BurstRender uses is frozen inside the folder at a version that's been tested together. Windows updates, Python updates, and the passage of time can't touch it.

### Linux

Install the four external tools from your distro, then BurstRender in a venv:

```bash
sudo apt install rawtherapee imagemagick ffmpeg libimage-exiftool-perl
git clone https://github.com/CharlesCage/burstrender
cd burstrender
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python burstrender.py --doctor   # verify all four tools resolve
```

RawTherapee must be ≥ 5.9 for CR3 support — any current distro qualifies. (If you used an older version of BurstRender: the Debian-unstable pinning dance from the old instructions is no longer needed, and please undo it if you did it. I'm sorry. I didn't know better at the time.)

The GUI works on Linux too, if you have Tk installed: `sudo apt install python3-tk`, then `.venv/bin/python burstrender_gui.py`.

## Using the GUI

The GUI walks you through the same workflow the CLI's [Best Practices](#best-practices) section describes, as three tabs you work left to right. A log pane at the bottom shows what's happening at every step.

**Tab 1 — Detect.** Pick the folder with your photos and where you want the output to go. Choose CR3 or JPG. Click **Detect Bursts** and you'll get a table of every burst found: start and end time, photo count, and orientation. Too many tiny bursts? Raise *Min photos per burst*. Bursts getting glued together? Lower *Gap between bursts*. Detect again — it's fast after the first scan.

**Tab 2 — Preview.** Click **Render Previews** to develop the first frame of each burst with the current settings, and flip through them with the arrows. This is where you tune the image: crop, gravity, normalization on/off, or a custom ffmpeg filter. Tweak, re-preview, repeat until they look right. (For the crop/gravity knobs, see [CR3 RAW Image Cropping](#cr3-raw-image-cropping) below for what the strings mean.)

**Tab 3 — Render.** Check the outputs you want — MP4, stabilized MP4, GIF — and click **Render All Bursts**. The top bar tracks bursts, the bottom bar tracks the current step (it counts frames during RAW conversion, the slow part, and pulses through the video stages). When it's done, **Open Output Folder** takes you to your files.

## Using the CLI

The CLI is identical on Windows (`burstrender.exe` from the bundle folder) and Linux (`.venv/bin/python burstrender.py` from the repo).

```
usage: burstrender [-h] [--source-path SOURCE_PATH] [--destination-path DESTINATION_PATH] [--seconds-between-bursts SECONDS_BETWEEN_BURSTS] [--minimum-burst-length MINIMUM_BURST_LENGTH] [--accept-jpg] [--detect-only] [--sample-images-only] [--no-stabilization] [--gif-only] [--no-normalize]
                   [--custom-vf-string CUSTOM_VF_STRING] [--crop-string CROP_STRING] [--gravity-string GRAVITY_STRING] [--doctor] [-q] [-v]

Render MP4s, Stabilized MP4s, and GIFs from burst CR3 RAW photos.

options:
  -h, --help            show this help message and exit
  --source-path SOURCE_PATH
                        Specify a source path for the input CR3 files. (If omitted, the current working directory is used.)
  --destination-path DESTINATION_PATH
                        Specify a destination path for rendered videos and/or gifs. (If omitted, the current working directory is used.)
  --seconds-between-bursts SECONDS_BETWEEN_BURSTS
                        Specify minimum time between detected bursts in seconds. (Default is 2.)
  --minimum-burst-length MINIMUM_BURST_LENGTH
                        Specify minimum number of photos in burst. (Default is 10.)
  --accept-jpg          Tell burtrender to look for bursts in JPG files. (Default is CR3.)
  --detect-only         Detect burst photos and display information only
  --sample-images-only  Render the PNG for first image of each burst only, apply any ffmpeg corrections, and move to destination path
  --no-stabilization    Do not stabilize the images
  --gif-only            Keep only final GIF and remove prelim MP4 files
  --no-normalize        Disable automatic normalization of the MP4 files via ffmpeg
  --custom-vf-string CUSTOM_VF_STRING
                        Specify a custom -vf string for ffmpeg. (Will come after scaling, speed, and normalization if not disabled. A preceding comma is not required.)
  --crop-string CROP_STRING
                        Specify a crop string for ImageMagick. (Default is 6000x4000+0+0.)
  --gravity-string GRAVITY_STRING
                        Specify a gravity string for ImageMagick. (Default is SouthEast.)
  --doctor              Check that all required external tools can be found, print versions, and exit
  -q, --quiet           Suppress progress bars
  -v, --version         Show program version

By Chuck Cage (chuckcage@corporation3355.org)
```

### Input and Output Paths

BurstRender assumes an input and output path of the current folder. However, you can specify these with the following arguments/parameters:

`--source-path` allows you to define where burstrender will look for the CR3 files to process. *Do not use a trailing /*.

`--destination-path` allows you to define where burstrender will place the final output files you've requested (e.g. PNG samples, MP4s, GIFs). *Do not use a trailing /*.

Note that unless you've requested sample PNGs via the `--sample-images-only` argument, all PNGs will be created in the working folder and will be removed after each burst conversion.

### Defining a "Burst"

BurstRender detects "bursts" by gathering the EXIF data from all the CR3s in the source folder, ordering them by the `EXIF:DateTimeOriginal` field supplemented with the `EXIF:SubSecTimeOriginal` field in order to capture time accurate enough for detecting up to ~100 FPS bursts, then grouping them into groups separated by gaps of more than two seconds. Additionally, it discards bursts of less than 10 images in order to prevent rendering MP4s and/or GIFs from groups too short to make interesting viewing.

However, you can tweak these knobs with the following arguments/parameters:

`--seconds-between-bursts` allows you to define the minimum gap between bursts in seconds. The default is *2*.

`--minimum-burst-length` allows you to specify the minimum number of images to qualify an image grouping as a "burst." The default is *10*.

### Accept JPG Files as Input

By default, burstrender will look for CR3 files. However, you can tell it to look for JPG files instead using the `--accept-jpg` flag. *Note: I only tested this with some images that came from a Nikon R8, so there might be issues if the files are small, differently-configured, etc.*

### Assistance in Preparing Batches

By default, burstrender will scan and detect bursts from all CR3s in the source folder, process them, and render GIFs and/or MP4s to the output folder. But you may wish to tweak the burst detection settings (above) or the image conversion (below) before setting burstrender loose on the entire conversion/rendering process. The following arguments/parameters are helpful:

`--detect-only` tells burstrender to perform the EXIF data extraction and burst detection processes and then output information about the detected bursts (specifically the start time, end time, and number of images) to the console, like this:

```
Detected 3 burst(s):
  Burst 1: 2024-02-16 14:14:19.280000 to 2024-02-16 14:14:19.760000 (50 photos, landscape)
  Burst 2: 2024-02-16 14:27:09.850000 to 2024-02-16 14:27:10.330000 (58 photos, landscape)
  Burst 3: 2024-02-16 14:28:24.710000 to 2024-02-16 14:28:25.190000 (55 photos, portrait)
```

Note that burstrender also detects portrait or landscape photos based on the `EXIF:Orientation` EXIF data field, and crops/scales each burst accordingly.

`--sample-images-only` tells burstrender to perform the EXIF data extraction and burst detection processes and then render *only the first image in each burst* directly to the output folder.

### CR3 RAW Image Cropping

Currently burstrender expects CR3s shot on a Canon R3. These Canon RAW files include black bars on the top and left of the image because the sensor area is larger than the output image. This information is included in the EXIF and gets automatically handled in most display applications. I couldn't figure out how to automatically detect and remove these, so right now burstrender just assumes the CR3s were shot at an intended 6000x4000 and applies a 6000x4000+0+0 crop with gravity set to SouthEast (i.e. it takes the bottom-right-most 6000x4000 pixels of the image).

If you are using a different camera and/or different settings and this doesn't work for you, OR you want to crop the image differently, you can use the following arguments/parameters to adjust ImageMagick's cropping of the CR3 file during conversion to PNG:

`--crop-string` allows you to directly specify an [ImageMagick crop string](https://www.imagemagick.org/Usage/crop/#crop_gravity) for the conversion. The default is *6000x4000+0+0* for landscape images or *4000x6000+0+0* for portrait images. Improperly formatted crop-string parameters may lead to errors in RAW conversion.

`--gravity-string` allows you to specify an [ImageMagick gravity setting](https://www.imagemagick.org/Usage/crop/#crop_gravity). The default is *SouthEast* for landscape images and *NorthEast* for portrait images.

Note that these strings should not include spaces and therefore also do not require quotes of any kind.

### Image Brightness, etc.

BurstRender uses `ffmpeg` to assemble the generated PNGs into an initial MP4. During this process it applies an internal [ffmpeg simple filtergraph](https://ffmpeg.org/ffmpeg.html#Filtering) ("`-vf`") of:

`scale=2000:-2,setpts=2.0*PTS` for landscape images or `scale=-2:2000,setpts=2.0*PTS` for portrait images.

...which scales the large PNGs down to a more reasonable 2000px largest side (while keeping aspect ratio) and slows the resulting video speed by half.

BurstRender also applies by default an [ffmpeg normalization string](https://ffmpeg.org/ffmpeg-filters.html#normalize) to the end of the filter above:

`,normalize=blackpt=black:whitept=white:smoothing=50`

However:

`--no-normalize` allows you to exclude the above normalization string, and

`--custom-vf-string` allows you to include your own customized [simple filter string](https://ffmpeg.org/ffmpeg-filters.html), which will be appended to the end of the initial one above (and following the normalization string, if you haven't disabled it with `--no-normalize`.) Note that you do not need to add a leading comma as burstrender will add it for you. You also should not include any spaces in your custom filter string, nor should you enclose it in quotes.

### Specifying Desired Output

By default burstrender will render for each detected burst:

* an MP4 movie `burst_X.mp4`
* a shake-stabilized MP4 movie `burst_X-stabilized.mp4`
* and a 480px looping GIF `burst_X.gif` (built from the stabilized MP4)

You can adjust this with the following arguments:

`--no-stabilization` specifies that you don't want to stabilize the resulting output. You will not receive the shake-stabilized MP4(s) and the GIF(s) you receive will not be stabilized.

`--gif-only` specifies that you only want GIFs. You will not receive either of the MP4s (but stabilization still runs behind the scenes so your GIFs stay smooth, unless you also pass `--no-stabilization`).

Note that burstrender will still need to make MP4s in order to create GIFs, but the required MP4s will be placed in the working folder and will be removed/cleaned up after execution.

### Utility Parameters

`--doctor` checks that all four required external tools (exiftool, RawTherapee, ffmpeg, ImageMagick) can be found, prints their versions, and exits. Run this first if something isn't working.

`--quiet` or `-q` mutes output to the console, which can be handy for CRON use, etc.

`--version` or `-v` outputs the version of burstrender you're using.

### Exit Codes

BurstRender provides standard exit codes to facilitate use in scripts. Codes are as follows:

| Exit Code | Description                 |
|-----------|-----------------------------|
| 0         | Success                     |
| 1         | Critical error              |
| 2         | Non-critical error          |

Specifically, burstrender will continue on all warnings and errors, but will exit immediately on critical errors. Additionally, if burstrender fails to produce any image combination renderings (i.e. MP4, stabilized MP4, or GIF), it will attempt to move any renderings successfully completed for the burst then skip to the next burst and continue.

### Best Practices

If you call burstrender from a folder containing CR3 files, it'll automatically:

* read the EXIF data from all the CR3s
* try to break them into bursts by looking for gaps of >2 seconds and eliminating bursts of less than 10 images
* produce a half-speed, 2000px-largest-side, normalized MP4
* produce a shake-stabilized MP4
* and produce a 480px-largest-side looping GIF
* all for each detected burst

However, if you want more control, you can try this process (this is exactly the loop the GUI's three tabs walk you through):

1. Execute burstrender with the `--detect-only` argument, along with any `--source-path` and `--destination-path` you need.

2. Look at the burst data returned. If you like it, go on to the next step. If not, add `--seconds-between-bursts` and/or `--minimum-burst-length` parameters to your command and run it again until you like the results.

3. Remove the `--detect-only` argument from your command (keeping any other changes) and add the `--sample-images-only` argument. Run the command again. This will generate PNGs from the first CR3 file in each burst.

4. Take a look at the generated PNGs. If you like them, move on to the next step. Otherwise, add the `--crop-string`, `--gravity-string`, `--custom-vf-string`, and/or `--no-normalize` arguments with parameters and run it again until you like the results.

5. Now remove the `--sample-images-only` argument and run the command to generate GIFs and/or MP4(s) for all the bursts.

## Troubleshooting

**First, always:** run `burstrender.exe --doctor` (Windows) or `.venv/bin/python burstrender.py --doctor` (Linux) from a terminal. It prints whether each of the four tools was found, where, and what version. A screenshot of that output answers most "it doesn't work" questions instantly.

**Logs.** The CLI writes logs to a `logs/` folder (next to the script on Linux; under `%LOCALAPPDATA%\burstrender\logs` for the Windows bundle). The GUI writes to `burstrender-gui.log` in that same Windows folder, and shows the important stuff in its log pane as it works.

**SmartScreen warning on Windows:** expected, once, because the bundle is unsigned. **More info → Run anyway.**

**"No bursts found":** your photos may be spaced wider than the 2-second default gap, or your bursts may be shorter than the 10-photo minimum. Use `--detect-only` (or the Detect tab) and tune from there.

## TODO

- [ ] Recursive folder search

## Contributing

This is my first real public repo, so I'm still figuring this out. If you want to contribute and know more than I do about it, LMK.

## License

This project is licensed under the [MIT License](LICENSE).
