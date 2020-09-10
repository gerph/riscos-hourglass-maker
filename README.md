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

* `artrayd1`: A bulbous hourglass which turns over, using just a single colour.
* `artrayd1-filled`: Same as `artrayd1`, but with a filled center.
* `artrayd1-bordered`: Same as `artrayd1-filled`, but with a border around it.
* `artrayd2`: Simple black hourglass which turns over, using just a sigle colour.
* `artrayd2-filled`: Same as `artrayd2`, but with filled center and bordered.
* `cog`: A SVG based cog which just turns, using a single colour.
* `cog-bordered`: Same as `cog-bordered`, but with a black border around it.

The difference between these hourglasses is essentially just the `source.gif` file, and the `build-shape.sh` which constructs the image data in `shape.py`.

## Building on RISC OS

```
dir <hourglass directory>
amu -f ^.MakefileROTest BUILD32=1
amu -f ^.MakefileROModule BUILD32=1
```
