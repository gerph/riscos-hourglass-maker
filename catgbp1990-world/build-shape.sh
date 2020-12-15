#!/bin/bash
##
# Constructs the shape.py file which describes the frames of the hourglass,
# from an existing hourglass.
#
# We trim the hourglass down, and convert it to a smaller number of colours,
# then we convert those results into:
#
#   * an animated gif of what it will look like
#   * a shape.py file which can be processed by makehourglass.py
#
# Requires:
#   ImageMagick
#   netpbm
#

set -e
set -o pipefail

pyhourglass="shape.py"

# Fields to exclude from the outputs (so that we don't get diffs every time we rebuild)
exclude_chunks=date,time
exclude_args=(-define png:exclude-chunks=${exclude_chunks})

# Extract the frames from the image
# Hourglass created by catgbp1990 - https://www.deviantart.com/catgbp1990/art/Pixel-Earth-718812255
convert "${exclude_args[@]}" source.gif -coalesce frame_%d.png

# RISC OS Classic cannot have pointers larger than 32 pixels wide.
width=64
height=64

# Set these to the active point, from top left (or empty to use the default of the center)
activex=
activey=

# Period between frames in centiseconds
frameperiod=3

# The palette to use for processing - green and blue
# These colours are very slightly different from one another to make their recognition possible by the
# naive palettising used later on.
palette=("0 0 0" "16 255 16" "0 0 254")

# The palette we take from the generated frames, which is different because we introduce another colour.
generatedpalette=("${palette[@]}")

# The palette to use for the actual hourglass
# Regular hourglass uses "255 255 255" "213 246 255" "0 161 255" "0 0 0".
# Standard pointer uses "255 255 255" "0 255 255" "0 0 153"
riscospalette=("0 0 0" "0 255 0" "0 0 255")
riscospalette[0]="192 192 192"


# Report we started
echo "Building hourglass 'shape.py' data"

# Report what we're using- different versions do act differently.
# v7.0.9 and v6.9.7 are known to work with these scripts - finding the right combinations of commands
# to work with both can be tricky.
echo "Using ImageMagick:"
convert -version 2>&1 | sed 's/^/  /'


# Generate the palette to use
cat > palette.ppm <<EOM
P3
${#palette[@]} 1
255
${palette[*]}
EOM

# Trim and reduce the image to limited colours
# - Shave off the edges to leave just the middle hourglass
# - Convert the colours down to just the palette we want to use
# - Make the white background transparent
for i in $( seq 0 29 ) ; do
    convert "${exclude_args[@]}" \
            frame_$i.png -shave 10x10 \
            -filter box -resize ${width}x${height} \
            -remap palette.ppm \
            -alpha on -fuzz 20% -transparent black -background black \
            +repage simple_$i.png
done

# Convert the frames into a GIF to see what it would look like
ordered_images=( $( seq 0 29 ) )
convert -delay "${frameperiod}" -dispose Background \
        $(for i in ${ordered_images[*]} ; do echo -n "simple_$i.png " ; done) animated.gif

# Now convert the PNGs to shapes that we may be able to use in shape.py
cat > "${pyhourglass}" << EOM
# Hourglass shape

width = $width
height = $height
activex = ${activex:-$((width / 2))}
activey = ${activey:-$((height / 2))}
frameperiod = $frameperiod

palette = []
images = []

EOM

# Colour translation regex for the pnm files
index=0
translation=$(for col in "${generatedpalette[@]}" ; do echo " ; s/$col/c${index}c/g" ; index=$((index+1)) ; done)
index=0
indextranslation=$(for col in "${riscospalette[@]}" ; do echo " ; s/c${index}c/${col}/g" ; index=$((index+1)) ; done)


for pal in "${riscospalette[@]}" ; do
    echo "palette.append(($(echo $pal | sed 's/ /, /g')))"
done >> "${pyhourglass}"
index=0
#echo "Translation: $translation"
for i in ${ordered_images[*]} ; do
    echo "images.append(("
    convert simple_$i.png ppm: \
        | (pnmtopnm -plain 2>/dev/null || pnmtoplainpnm) \
        | sed -e "1,3 d; /^$/ d $translation ; s/c//g; s/ //g" \
        | perl -e '$in=join "", <STDIN>; $in =~ s/\n//g; for $row ($in =~ /(.{'$width'})/g) { print "        \"$row\",\n"; }'
    echo "    ))"
done >> "${pyhourglass}"

# Provide a single example frame which is the right colours
convert simple_0.png ppm: \
    | (pnmtopnm -plain 2>/dev/null || pnmtoplainpnm) \
    | sed -e "$translation ; $indextranslation" \
    | tee example.pnm \
    | convert - example.png
