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

Apologies for the manual/crappy way this installation works. I'm still learning to deploy Python well. Right now it's important to know that this is only designed to work on Linux or on the Debian WSL system under Windows. I've deployed to both with success following these instructions. TODO: package this properly.

And yes, this is pretty hacky. If you wish to improve, please share.

### Install RawTherapee

Need to install 5.9 or later. This is in Debian 12 ("Bookworm"). 
Check with apt list rawtherapee

1. Check to see if RawTherapee is already installed by issuing the `rawtherapee-cli` command. If RawTherapee responds, you're good to go.

2. Otherwise, install RawTherapee with `sudo apt install rawtherapee` or whatever works for your distro.
   
3. Repeat #1 above to make sure `rawtherapee-cli` responds.

If you're installing to Debian WSL under Windows, you're probably stuck with Debian 11 ("Bullseye"). Sadly this is oldstable as of March 2024, and it only provides version 5.8. If so, you have a couple of options.

#### Option 1: Install from Unstable

**BE CAREFUL. YOU CAN EASILY BUILD FRANKENDEBIAN IF YOU'RE NOT CAREFUL. YOU HAVE BEEN WARNED.**

Seriously, this worked for me, but do it at your own risk. For this example, I'm installing on Debian WSL.

1. Before you do all this, make sure to `sudo apt update` and `sudo apt upgrade` to make sure everything is current with your WSL install.

1. Edit your `/etc/apt/sources.list` file to add Debian unstable.

   On current Debian WSL, the file should look something like this:

   ```
   deb http://deb.debian.org/debian bullseye main non-free contrib
   deb http://deb.debian.org/debian bullseye-updates main non-free contrib
   deb http://security.debian.org/debian-security bullseye-security main non-free contrib
   deb http://ftp.debian.org/debian bullseye-backports main non-free contrib
   ```

   Edit it (with `sudo`, of course, since `/etc/apt/` is owned by `root`). Add the following line:

   `deb http://deb.debian.org/debian unstable main non-free contrib`

   Save the file.

2. Create the file `/etc/apt/preferences` in order to use pinning to prevent Debian from trying to update your entire install to unstable.

   Put the following text in the file:

   ```
   Package: *
   Pin: release a=oldstable
   Pin-Priority: 900

   Package: *
   Pin: release a=unstable
   Pin-Priority: 100
   ```

   This essentially says "default everything to oldstable (what WSL currently uses) but let me request installing packages from unstable."

   Save the file.

3. Update the package library with `sudo apt update`.

   LOOK CAREFULLY at the output to confirm that "All packages are up to date." This should be the case since you updated/upgraded everything before starting this process. If you see this, you're ready to go to the next step.
   
   If insteaad it shows a kajillion packages requiring update, something is screwed up. You'll need to **fix it BEFORE you do an upgrade** or you're probably screwed. Worst case scenario, you can remove the line in `/etc/apt/sources.list` you added in #1 above, remove the `/etc/apt/preferences` file you created in #2, and re-run a `sudo apt update` . If you're back to "All packages are up to date." then you can start over and try again or abandon pinning and try something else.

4. Install rawtherapee from unstable with the command `sudo apt install -t unstable rawtherapee`.

   As of today, this installed v5.10 for me along with a bunch of dependencies from unstable. So far it doesn't seem to have broken anything else, though there's always a risk with mixing releases.

5. Check to see if the installed app starts with the command `rawtherapee-cli`. It should respond without errors.

#### Option 2: Build RawTherapee from Source

Instructions are [here](https://rawpedia.rawtherapee.com/Linux).

#### Option 3: ???

If for some reason RawTherapee is not in your distribution, you can potentially get it [here](https://rawtherapee.com/) as a Linux AppImage and source code. If you install it as an AppImage or compile it from source you'll want to make sure it ends up in your PATH such that you can execute it as your user (the one you intend to run burstrender with) from anywhere. You can test this with #1 above.

### Test RawTherapee

When you're all done, let's run a test to convert a CR3 to a PNG to make sure everything is good. Use the command:

`rawtherapee-cli -o "YOUR_OUTPUT_PATH_AND_FILE.png" -n -Y -c "YOUR_INPUT_RAW.CR3"`

You should get a PNG. Open it up in Windows and it should look like the CR3 image. If so, you're good to move on with the install. If the image is all white, you probably have an old version of RawTherapee, or at least something older than v5.9. When I first tried it with v5.8 that comes in Debian oldstable (v5.8) this happened to me.

### Install ImageMagick

1. Check to see if ImageMagick is already installed by issuing the `convert` command. If convert responds, you're good to go.

2. Otherwise, install ImageMagick with `sudo apt install imagemagick` or whatever works for your distro.
   
3. Repeat #1 above to make sure convert responds. Pretty much every distro in existence seems to have ffmpeg, but if for some reason you compile it from source or install it via other mechanisms, be sure to make sure it's in your PATH such that you can execute it as your user (the one you intend to run burstrender with) from anywhere. You can test this with #1 above.

### Configure ImageMagick for RAW

ImageMagick can't handle RAW files out of the box, at least not in most available versions. And some versions that handle RAW don't handle CR3s. I avoid this problem by adding RawTherapee as a helper for ImageMagick RAW file processing. There are other possibilities, including adding various RAW libraries and compiling some of the latest versions of ImageMagick from source. See the resource below if you want/need to try that method. But this worked great for me and involed less mess.

1. Find ImageMagick's `delegates.xml` file.

   On both Debian 12 and a Debian WSL install I found mine in `/etc/ImageMagick-6/delegates.xml`, so you might check thereabouts and get lucky.

   If not, you can try the command `find / -name delegates.xml`, but it can take a long time. You can always try `/etc` instead of `/` first, too. Or try the method below.
   
   If you find multiple `delegates.xml` files (I didn't, thankfully!) or you just want to try this method first, you may have some luck with the command `convert -debug "all" abc.xyz test.jpg`. This will produce a ton of console logging output from ImageMagick, and you can look for a `Loading delegate configure file:` line which should tell you which file ImageMagick is actually using.

2. Edit the `delegates.xml` file.
   
   Note the ownership of the file. If it's owned by `root` you'll need to use `sudo`.

   You may also want to protect yourself by first making a copy of `delegates.xml` to a file in the same place named `delegates.xml.old`. Very helpful if you rrun into problems.

   Our goal here is to add RawTherapee as a helper app for DNG fiiles (which will also handle our CR3s). I had luck searching for `dng` in the `delegates.xml` file. If you find a line with something like `<delegate decode="dng:decode"...`  you'll want to modify it to match the line below. If you don't find such a line, add the line below in the `<delegatemap>` section of the file:

   `<delegate decode="dng:decode" command="&quot;rawtherapee-cli&quot; -o &quot;%u.png&quot; -n -Y -c &quot;%F&quot;"/>`

   Some additional help if you're doing this in WSL: you may need to enable Copy/Paste within the WSL shell (or [mintty]([https://](https://mintty.github.io/) if you're using that). In most of them it's under Options/Options or sometimes (like in mintty) under Options/Text. These enable you to use `Ctrl+Shift+V` to paste from the Windows clipboard, so you can copy the line above and paste it into your terminal edit app (probably vim or nano),

3. Test the new ImageMagick configuration.

   Grab a CR3 and try to convert it to a PNG directly with ImageMagick using the following command:

   `convert -debug "all" your-file-here.CR3 test.PNG`

   If all goes well you should get an output PNG, and you should see a `rawtherapee-cli` command in the spew of console logging.

If this doesn't work, [this is a great resource](https://www.isoftstoneinc.com/insights/libraw-rawtherapee-imagemagick/) for understanding how the whole process works and what you might need to do in order to make it work for your potentially unique ImageMagick and RawTherapee installation.

### Install ffmpeg

1. You may already have ffmpeg installed. It's pretty damn common. Check by issuing the command `ffmpeg`. If it's installed, you're good to go.
   
2. If not, install it via `sudo apt install ffmpeg` or whatever works for your distro. You shouldn't need any special version of this as all the features used here have been in the package for a long time.

### Install exiftool

`sudo apt install exiftool` or whatever works for your distro.

### Clone the Repo

1. If you don't already have git installed, install it with `sudo apt install git`.
   
2. Clone this repo into somewhere safe, like maybe underneath `~/github` in your home folder. It doesn't matter where you put it, but this is probably the easiest. If you're sitting in the location you want to clone, issue the command `git clone https://github.com/CharlesCage/burstrender`.

### Check config.yaml

Burstrender reads some basic parameters from a config.yaml file. Check the included file to adjust the defaults as needed for your install. Specifically:

* The default working folder is set to `~/.burstrender/working`. Make sure this location (or whatever location you choose) can accommodate at minimum the PNGs, MP4s, and GIF for the largest burst you process. (Burstrender cleans up the created PNGs and moves the MP4s and GIF to the output folder after processing each burst.) If the selected location doesn't exist, burstrender will try to create it.

* The default logging path is the `logs` folder underneath the location where you cloned this repo. Burstrender automatically rotates log files when they reach 10 MB, and 10 log files are kept before they are deleted. (So the total log storage should never be that large.) You can specify anywhere you like for the logs, but make sure the user that will run burstrender has the appropriate permissions for the log location.

### Make Sure You Have Python3.11.x

1. Execute the command `python3 --version`. If you're on Debian 12, you're fine. If you're installing to Debian WSL, you'll have something older.
   
2. As of now, Python3.11 is in unstable, so if you followed the pinning instructions above successfully, you should be able to install it with:

   `sudo apt install -t unstable python3`

   Check it again if needed and confirm that it's installed. And yes, this might break things. It didn't for me, but pay attention.

### Create/Activate .venv Virtual Environment

1. Change directories to the location where you git cloned the repo. In the example here, we put it in `~/github/burstrender`. So for that you'd `cd ~/github/burstrender`.

2. Install python3-venv with the command `sudo apt install python3-venv`.

   If you're on Debian WSL and installed Python3.11 above, use the command `sudo apt install python3.11-venv` instead.

3. Create the virtual environment with the command `python3 -m venv .venv`.

4. Activate the .venv virtual environment there with the command `source .venv/bin/activate`.

   Your prompt should now be preceeded with `(.venv)` and maybe look something like `(.venv) chuckcage@joshua:~/github/burstrender$`.

### Install Requirements

Ok. If you're on Debian WSL this gets just super fun and complicated. If you're on Debian 12, you can probably just skip to the `pip3 install -r requirements.txt` command below. Otherwise, make sure you're still in the burstrender folder with the virtual environment activated (from previous step) and here we go:

1. Install wheel with pip: `pip3 install wheel`
   
2. Install all the build requirements for the py3exiv2 pip package:

   `sudo apt-get install build-essential python-all-dev libexiv2-dev`

3. Install the remaining build requirement for py3exiv2, libboost-python-dev. BUT, this one needs to come from unstable. And it conflicts with other packages. I was able to make it work by using aptitude and letting it figure out how to solve the dependency problem.

   Start with `sudo apt install aptitude`.

   Then `sudo aptitude install -t unstable libboost-python-dev`. You SHOULD be able to accept the default solutions it provides. If all goes well, you end up with the package installed.

Finally we can:

4. Install the requirements with the command `pip3 install -r requirements.txt`.

   Hopefully this installs everything, takes a while to build py3exiv2, and you get all happy white text. If it spews red, you'll need to troubleshoot. DuckDuckGo is your friend.
   
5. Deactivate the .venv virtual environment with the command `deactivate`.

### Edit the burstrender Script

In order to allow execution of burstrender.py within the .venv virtual environment from anywhere and without calling the python instance, this file is a shell script designed to do all that for you. But you need to do a few things to get it working.

1. Edit the `burstrender` script file provided with the repo and adjust the paths so that they reference the location in which you put the git clone of this repo. NOTE that this is not the burstrender folder, but rather the burstrender file within the burstrender folder. If you cloned the repo to `~/github/burstrender` then just change both lines in the file from `~/gitlab/burstrender` to `~/github/burstrender` or wherever you put it.
   
2. Make the `burstrender` script executable with the command `chmod +x burstrender` or whatever works for your distro.

3. Test the script by executing it. If you're still in the burstrender folder, try `./burstrender`. Since there are no CR3 files provied in the repo, you should get a message that no CR3 files were found in the source path. If you get other errors, troubleshoot.

### Add a Symlink for the burstrender Script

1. Find a location that's in your PATH. The easiest way to do this is to open a shell and type `$PATH`. A common location for this would be `/home/YOURUSER/.local/bin`. But YMMV. Find a place in the path that you're comfortable placing a symlink referencing the `burstrender` script.
   
2. Create the symlink from the burstrender script to your chosen target location from #1 above. For example, if you cloned the repo to `~/github/burstrender` and you chose `/home/YOURUSER/.local/bin` above, you'd use the command:
   
   `ln -s /home/YOURUSER/github/burstrender/burstrender /home/YOURUSER/.local/bin/`
   
   (If you chose somewhere owned by root, use `sudo`.)

### Test Your Install

Test the install by executing `burstrender -h` from somewhere outside the place you put the symlink or the place you put the cloned repo. You should see the help output from burstrender.

And you're ready to go!

## Usage
```
usage: burstrender [-h] [--source-path SOURCE_PATH] [--destination-path DESTINATION_PATH]
                   [--seconds-between-bursts SECONDS_BETWEEN_BURSTS] [--minimum-burst-length MINIMUM_BURST_LENGTH]
                   [--detect-only] [--sample-images-only] [--no-stabilization] [--gif-only] [--modulate-string MODULATE_STRING]
                   [--crop-string CROP_STRING] [--gravity-string GRAVITY_STRING] [-q] [-v]

Render MP4s, Stabilized MP4s, and GIFs from burst CR3 RAW photos.

options:
  -h, --help            show this help message and exit
  --source-path SOURCE_PATH
                        Specify a source path for the input CR3 files. (If omitted, the current working directory is used.)
  --destination-path DESTINATION_PATH
                        Specify a destination path for rendered videos and/or gifs. (If omitted, the current working directory is
                        used.)
  --seconds-between-bursts SECONDS_BETWEEN_BURSTS
                        Specify minimum time between detected bursts in seconds. (Default is 2.)
  --minimum-burst-length MINIMUM_BURST_LENGTH
                        Specify minimum number of photos in burst. (Default is 10.)
  --detect-only         Detect burst photos and display information only
  --sample-images-only  Render the PNG for first image of each burst only
  --no-stabilization    Do not stabilize the images
  --gif-only            Keep only final GIF and remove prelim MP4 files
  --modulate-string MODULATE_STRING
                        Specify a modulate string for ImageMagick. (Default is 120.)
  --crop-string CROP_STRING
                        Specify a crop string for ImageMagick. (Default is 6000x4000+0+0.)
  --gravity-string GRAVITY_STRING
                        Specify a gravity string for ImageMagick. (Default is SouthEast.)
  -q, --quiet           Suppress progress bars
  -v, --version         Show program version

By Chuck Cage (chuckcage@corporation3355.org)
```
### Input and Output Paths

Burstrender assumes an input and output path of the current folder. However, you can specify these with the following arguments/parameters:

`--source-path` allows you to define where burstrender will look for the CR3 files to process. *Do not use a trailing /*.

`--destination-path` allows you to define where burstrender will place the final output files you've requested (e.g. PNG samples, MP4s, GIFs). *Do not use a trailing /*.

Note that unless you've requested sample PNGs via the `--sample-images-only` argument, all PNGs will be created in the working folder and will be removed after each burst converstion.

### Defining a "Burst"

Burstrender detects "bursts" by gathering the EXIF data from all the CR3s in the source folder, ordering them by the `EXIF:DateTimeOriginal` field supplemented with the `EXIF:SubSecTimeOriginal` field in order to capture time accurate enough for detecting up to ~100 FPS bursts, then grouping them into groups separated by gaps of more than two seconds. Additionally, it discards bursts of less than 10 images in order to prevent rendering MP4s and/or GIFs from groups too short to make interesting viewing. 

Howevver, you can tweak these knobs with the following arguments/parameters:

`--seconds-between-bursts` allows you to define the minimum gap between bursts in seconds. The default is *2*.

`--minimum-burst-length` allows you to specify the minimum number of images to qualify an image grouping as a "burst." The defaults is *10*.

### Assistance in Preparing Batches

By default, burstrender will scan and detect bursts from all CR3s in the source folder, process them, and render GIFs and/or MP4s to the output folder. But you may wish to tweak the burst detection settings (above) or the image conversion (below) before setting burstrender loose on the entire conversion/rendering process. The following arguments/parameters are helpful:

`--detect-only` tells burstrender to perform the EXIF data extraction and burst detection processes and then output information about the detected bursts (specifically the start time, end time, and number of images) to the console, like this:

```
Detected 3 burst(s):
  Burst 1: 2024-02-16 14:14:19.280000 to 2024-02-16 14:14:19.760000 (50 photos)
  Burst 2: 2024-02-16 14:27:09.850000 to 2024-02-16 14:27:10.330000 (58 photos)
  Burst 3: 2024-02-16 14:28:24.710000 to 2024-02-16 14:28:25.190000 (55 photos)
```

`--sample-images-only` tells burstrender to perform the EXIF data extraction and burst detection processes and then render *only the first image in each burst* directly to the output folder. 

### CR3 RAW Image Cropping

Currently burstrender expects CR3s shot on a Canon R3. These Canon RAW files include black bars on the top and left of the image because the sensor area is larger than the output image. This information is included in the EXIF and gets automatcially handled in most display applications. I couldn't figure out how to automatically detect and remove these, so right now burstrender just assumes the CR3s were shot at an intended 6000x4000 and applies a 6000x4000+0+0 crop with gravity set to SouthEast (i.e. it takes the bottom-right-most 6000x4000 pixels of the image). 

If you are using a different camera and/or different settings and this doesn't work for you, OR you want to crop the image differently, you can use the following arguemnts/parameters to adjust ImageMagick's cropping of the CR3 file during conversion to PNG:

`--crop-string` allows you to directly specify an [ImageMagick crop string](https://www.imagemagick.org/Usage/crop/#crop_gravity) for the conversion. The default is *6000x4000+0+0*.

`--gravity-string` allows you to specify an [ImageMagick gravity setting](https://www.imagemagick.org/Usage/crop/#crop_gravity). The default is *SouthEast*.

Note that these strings should not include spaces and therefore also do not require quotes of any kind.

### Image Brightness, etc.

During the conversion from CR3 RAW to PNG, burstrender applies the [auto-level](https://imagemagick.org/script/command-line-options.php?#auto-level) parameter to ImageMagick, which essentially stretches the minimum and maximum color values in teh image to 0% and 100%, and sets a modulation of 120, which adds 20% bringness to the image.. This seems to do a pretty decent job of bringing the RAW to a viewable state.

However, you can tweak with the follwoing arugments/parameters:

`--modulate-string` allows you to specify an [ImageMagick modulate string](https://imagemagick.org/Usage/color_mods/#modulate) for the conversion. The defailt is *120*.

### Specifying Desired Output

By default burstrender will render for each detected burst:

* an MP4 movie `burst_X.mp4`
* a shake-stabilized MP4 movie `burst_X-stabilized.MP4`
* and a GIF `burst_X.gif`

You can adjust this with the following arguments:

`--no-stabilization` specifies that you don't want to stabilize the resulting output. You will not receive the shake-stabilized MP4(s) and the GIF(s) you receive will not be stabilized.

`--gif-only` specifies that you only want GIFs. You will not receive either of the MP4s.

Note that burstrender will still need to make MP4s in order to create GIFs, but the required MP4s will be placed in the working folder and will be removed/cleaned up after execution.

### Utility Parameters

`--quiet` or `-q` mutes output to the console, which can be handy for CRON use, etc.

`--version` or `-v` oututs the version of burstrender you're using

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
4. Take a look at the generated PNGs. If you like them, move on to the next step. Otherwise, add the `--modulate-string`, `--crop-string`, and/or `--gravity-string` arguments with parameters and run it again until you like the results.
5. Now remove the `--sample-images-only` argument and run the command to generate GIFs and/or MP4(s) for all the bursts.

## TODO

- [ ] Package for at least semi-easy deployment. NO REALLY.

## Contributing

This is my first real public repo, so I'm still figuring this out. If you want to contribute and know more than I do about it, LMK.

## License

This project is licensed under the [MIT License](LICENSE).
