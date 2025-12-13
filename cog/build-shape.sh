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
srcsize=124x124
degrees=5
rotations=8
for step in $(seq 0 ${rotations}) ; do
    magick "${exclude_args[@]}" -size ${srcsize} source.svg \
            -distort SRT $(( step * degrees )) +repage frame_${step}.png
done

# RISC OS Classic cannot have pointers larger than 32 pixels wide.
width=32
height=32

# Set these to the active point, from top left (or empty to use the default of the center)
activex=
activey=

# Period between frames in centiseconds
frameperiod=3

# The palette to use for processing - 3 greens
#palette=("255 255 255" "0 153 14" "0 74 0" "0 228 0")
# The 3 greens palette won't work because the image has a 3D effect applied that is wrong
# as you rotate. So just use 1 green.
palette=("255 255 255" "0 153 14")

# The palette we take from the generated frames
generatedpalette=("${palette[@]}")

# The palette to use for the actual hourglass
# Regular hourglass uses "255 255 255" "213 246 255" "0 161 255" "0 0 0".
# Standard pointer uses "255 255 255" "0 255 255" "0 0 153"
riscospalette=("${generatedpalette[@]}")
riscospalette[0]="192 192 192"


# Report we started
echo "Building hourglass 'shape.py' data"

# Report what we're using- different versions do act differently.
# v7.0.9 and v6.9.7 are known to work with these scripts - finding the right combinations of commands
# to work with both can be tricky.
echo "Using ImageMagick:"
magick -version 2>&1 | sed 's/^/  /'


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
for i in $( seq 0 ${rotations} ) ; do
    magick "${exclude_args[@]}" \
            frame_$i.png \
            -resize ${width}x${height} +dither \
            -remap palette.ppm \
            -alpha on -fuzz 20% -transparent white -background white \
            +repage simple_$i.png
done

# Convert the frames into a GIF to see what it would look like
ordered_images=( $( seq 0 ${rotations} ) )
magick -delay "${frameperiod}" -dispose Background \
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
    magick simple_$i.png -compress none -depth 8 ppm:- \
        | (pnmtopnm -plain 2>/dev/null || pnmtoplainpnm) \
        | sed -e "1,3 d; /^$/ d $translation ; s/c//g; s/ //g" \
        | perl -e '$in=join "", <STDIN>; $in =~ s/\n//g; for $row ($in =~ /(.{'$width'})/g) { print "        \"$row\",\n"; }'
    echo "    ))"
done >> "${pyhourglass}"

# Provide a single example frame which is the right colours
magick simple_0.png -compress none -depth 8 ppm:- \
    | (pnmtopnm -plain 2>/dev/null || pnmtoplainpnm) \
    | sed -e "$translation ; $indextranslation" \
    | tee example.pnm \
    | magick - example.png
