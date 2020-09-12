# RISC OS Hourglass building

This repository contains some hourglass modules for RISC OS.

The modules are constructed from animated GIFs through a number of transformations:

* The GIF is split into its compnent frames using ImageMagick.
* The frames processeed into what will be used as the frames of the hourglass:
    * They are trimmed to remove borders.
    * Colour are changed to reduce the colours to the 3 available on RISC OS.
    * Shape transformations may add borders.
    * The background is made transparent.
* An animated GIF of the result is constructed.
* The frames are quantised into the 4 palette colours and written into a python module.
* The python module is used to generate sources which can make the frames appear:
    * A BASIC program that applies the frames sequentially.
    * An assembler library that can be used to set the frames.
* RISC OS AMU files are then invoked to build this into code:
    * A standalone C program calls the library, in a similar manner to the BASIC code.
    * A module is built which calls the library when the Hourglass SWIs are called.

The result is that from a single `make` command, RISC OS hourglasses are made from GIFs.
The full build process requires cross compiling tools, but the repository contains the outputs sufficient that the sources may build on RISC OS.

## Enclosed hourglasses

### Animated hourglasses

* `artrayd1`: A bulbous hourglass which turns over, using just a single colour.
* `artrayd1-filled`: Same as `artrayd1`, but with a filled center.
* `artrayd1-bordered`: Same as `artrayd1-filled`, but with a border around it.
* `artrayd2`: Simple black hourglass which turns over, using just a sigle colour.
* `artrayd2-filled`: Same as `artrayd2`, but with filled center and bordered.
* `cog`: A SVG based cog which just turns, using a single colour.
* `cog-bordered`: Same as `cog-bordered`, but with a black border around it.
* `catgbp1990`: A rotating earth.

### Static hourglasses

* `nkozin`: Simple hourglass beside a pointer, unfilled.
* `nkozin-filled`: Same as `nkozin`, but with a filled centre.

The difference between these hourglasses is essentially just the `source.gif` file, and the `build-shape.sh` which constructs the image data in `shape.py`.

## Building on RISC OS

```
dir <hourglass directory>
amu -f ^.MakefileROTest BUILD32=1
amu -f ^.MakefileROModule BUILD32=1
```

## Creating a new hourglass

- Locate your source image - a PNG, GIF, SVG or similar.
    - PNG and SVG are ok for some images, and might be good for static or simple rotation (like the cog), but an animated GIF gives more options.
- Create a new directory for the hourglass.
- Copy the source image as `source.EXT`.
- Copy one of the `build-shape.sh` scripts from an existing directory.
    - If you're processing an SVG, cog example should be suitable.
    - If you're processing a GIF, the other animated examples should be suitable.
- Change the `build-shape.sh` until you have a set of simple frames you like; lots of bits you can do here:
    - The initial extraction of the images has a `convert` command that either extracts the PNG, extracts many frames from a GIF or rotates the SVG. This will need modifying to make `frame_#.png` that we will work work. This is the source for each frame we create, so it needs to be large enough to rescale well, but we don't need to worry too much about colours.
    - Update the `width` and `height` to the width and height you want the hourglass to be - remember that RISC OS Classic only supports hourglasses up to 32 pixels wide. The aspect ratio of the output should probably match the aspect ratio of the input if you want to keep the same shape of the image.
    - Update the `activex` and `activey` to the position of the active point on the hourglass. Usually this is the centre of the hourglass, for which you can just leave the values empty and it will be calculated from the width and height (rounded down).
    - Update the `frameperiod` with how long you want between frames in centiseconds. Usually you'll leave this as 2 or 3 and then update it at the end once you've worked out how well it works.
    - Update the `palette` to reflect the colours you want to process out of the source image. These are up to 4 colours (the first of which should be white, or the background colour) which will be taken from the source image - all the rest will be quantised to those 4. They don't have to be the final image colours, but they should be the primary colours you want to extract.
    - Update the `generatedpalette` to reflect the colours you're going to make. This is a little more complicated, but essentially if you're adding or changing colours in the subsequent processing stage, that's where you'd add those colours. Normally you leave this as the same as the `palette` and come back later to add new colours if necessary.
    - Update the `riscospalette` to the colours you want to use in the hourglass. The colours you generate in the processing step will be extracted, but you can use any colours your like for the results, so an hourglass that was originally red can actually get coloured as blue by setting the colour to red in the `generatedpalette` (and maybe `palette`), but blue for that colour index in `riscospalette`.
    - Look at the 'Trim and reduce' section which processes the `frame_#.png` images into `simple_#.png` (which are images we will actually use). This is the most complicated part of the process because ImageMagick is not easy to work with at times, but very powerful.
        - Firstly, the loop has to reference all the frames so that we process them all (assuming you want to process them all - you can select just certain frames if you want, but usually you'll process all of them). The `$(seq 0 #)` command needs updating so that all the frame numbers are processed.
        - Now the processing of the image in the convert statement needs to be updated; this is more tricky. You will almost certainly need to consult the ImageMagick documentation if you are doing anything more then tweaking the image here. The CI system uses ImageMagick 6.9, and if you've got ImageMagick 7 installed you may find differences, particularly in the handling of the alpha channel.
        - There are examples of different operations in the supplied hourglasses. This is why they get more complex - so you can see what's changed between them.
            - Filling: Automatic filling of the shape is used in many of them, but is easiest to see in `artrayd1-filled`. However, sometimes the automatic filling doesn't work, and it's necessary to manually fill a shape, which is demonstrated in `nkozin-filled`.
            - Bordering: Bordering is given as an example on top of that in `artrayd1-bordered`, but also in the `cog-bordered` hourglass. Shaving is performed on most of the hourglasses.
        - There are many ugly effects you can get due to the scaling and misalignment of pixels, and there are many problems caused by the lack of colours. Try to make the hourglass line up to the pixel grid where possible, so that there aren't jagged edges, and try to get the scaling such that horizontal and vertical lines don't change in shape due to grid alignment issues. This is why it's commonly better to draw these small icons by hand.
        - You could replace this whole section with more intelligent generation code. So long as you get out frames in `simple_#.png`, they can be made into an hourglass.
    - Update the `ordered_images` to give the correct order for the frames. This is usually a set of `seq <start> <end>` commands which list the frames to use in the final image. It is common for the animation to not start where you want it to, so reordering the images is useful - this is the case for some of the hourglasses whose source images start out by rotating, but we want them to start with falling sand. Similarly, repeating some frames can make them static for longer, which is used in the artrayd hourglasses to make the final clump of sand stay put before rotating.
    - Throughout these changes, running the script and then seeing what comes out in the `simple_#.png` files is a tedious but expected process.
- Symlink the Makefile to the one at the root of the repository; this means that the same build process will be run for the job.
    - `ln -s ../MakefileForHourglass Makefile`
- Run the whole build with `make`. If you don't have the cross-compiling RISC OS tools, use `make USE_ROBUILD=1` to generate the RISC OS modules using the build.riscos.online service.
- Check the results on RISC OS.
    - Run the `hourglass_basic` program to check that it does the right thing.
    - Run the `aif32.hourglass_test` program to check that the assembler has been built correctly.
    - Load the `rm32.Hourglass` module and issue `*Hon` to check that it behaves as expected.
- Rinse and repeat.
- If you're really happy with the hourglass, why not add it to the main repository:
    - Update the top level `Makefile` to add the directory name to the `HOURGLASSES` variable.
    - Run `make` (or `USE_ROBUILD=1 make` if you don't have the cross-compiling tools).
        - Wait for all the hourglasses to build!
    - Check that the `artifacts` directory now includes your new hourglass module.
    - Update this `README.md` to describe your hourglass.
    - Commit it all to git.
        - Usually I squash the changes down to a single change (or structured set of changes), to make the history easier.
        - Make sure that the generated files that aren't ignored are also committed. This allows anyone without access to the build process (specifically ImageMagick, but also Python) to still build the hourglass.
    - Create a PR.
        - Usually you'd fork the github repository, push and then create a pull request for the changes. This process is outside the scope of this document.
