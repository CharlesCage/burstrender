# BurstRender

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Description

BurstRender analyzes a folder full of CR3 photos (shot with a Canon R3), identifies bursts of photos, and then automates RawTherapee, ImageMagick, and ffmpeg to render each of the bursts as an MP4, a motion-stabilized MP4, and a GIF. It's kinda hacky, but I threw it together for a friend who photographs his daughter's softball team and wanted an easy way to generate parent- and player-friendly movies and GIFs from the thousands of photos he shoots at each game.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [TODO](#todo)
- [Contributing](#contributing)
- [License](#license)

## Installation

Instructions on how to install and run your project.

## Usage
```
usage: burstrender [-h] [--source-path SOURCE_PATH] [--destination-path DESTINATION_PATH] [--seconds-between-bursts SECONDS_BETWEEN_BURSTS] [--minimum-burst-length MINIMUM_BURST_LENGTH]
                   [--detect-only] [--sample-images-only] [-ns] [--gif-only] [-q] [-v]

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
  --detect-only         Detect burst photos and display information only
  --sample-images-only  Render the PNG for first image of each burst only
  -ns, --no-stabilization
                        Do not stabilize the images
  --gif-only            Keep only final GIF and remove prelim MP4 files
  -q, --quiet           Suppress progress bars
  -v, --version         Show program version

By Chuck Cage (chuckcage@corporation3355.org)
```

### Best Practices

If you call burstrender from a folder containing CR3 files, it'll automatically 

* read the EXIF data from all the CR3s
* try to break them into bursts by looking for gaps of >2 seconds and eliminating bursts of less than 10 images
* produce a half-speed, 2000px-wide MP4
* produce a slightly-less-than-2000px-wide shake-stabilized MP4
* and produce a 1000px-wide looping GIF
* all for each detected burst

However, if you want more control, you can try this process:

1. Execute burstrender with the `--detect-only` argument, along with any `--source-path `and `--destination-path` you need.
2. Look at the burst data returned. If you like it, go on to the next step. If not, add `--seconds-between-bursts` and/or `--minimum-burst-length` parameters to your command and run it again until you like the results.
3. Remove the `--detect-only` argument from your command (keeping any other changes) and add the `--sample-images-only` argument. Run the command again. This will generate PNGs from the first CR3 file in each burst.
4. Take a look at the generated PNGs. If you like them, move on to the next step. Otherwise, add the TK argument with parameters and run it again until you like the results.
5. Now remove the `--sample-images-only` argument and run the command to generate GIFs and/or MP4(s) for all the bursts.

## TODO

- [ ] Package for at least semi-easy deployment

## Contributing

Guidelines on how to contribute to your project.

## License

This project is licensed under the [MIT License](LICENSE).
