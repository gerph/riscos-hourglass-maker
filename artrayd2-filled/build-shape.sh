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

pyhourglass="shape.py"

# Fields to exclude from the outputs (so that we don't get diffs every time we rebuild)
exclude_chunks=date,time
exclude_args=(-define png:exclude-chunks=${exclude_chunks})

# Extract the frames from the image
# Hourglass created by artrayd, from https://dribbble.com/shots/10777708-Sand-Clock-Loader-Animation
convert "${exclude_args[@]}" source.gif -coalesce frame_%d.png

# RISC OS Classic cannot have pointers larger than 32 pixels wide.
width=32
height=32

# Period between frames in centiseconds
frameperiod=2

# The palette to use for processing - just a black (and maybe a grey)
#palette=("255 255 255" "0 0 0" "128 128 128" "64 64 64")
palette=("255 255 255" "0 0 0")

# The palette we take from the generated frames, which is different because we introduce another colour.
generatedpalette=("255 255 255" "173 219 230" "0 0 0")

# The palette to use for the actual hourglass
realpalette=("255 255 255" "255 255 255" "0 0 0") # White inside, black outside

# Generate the palette to use
cat > palette.ppm <<EOM
P3
# Blue palette
${#palette[@]} 1
255
${palette[*]}
EOM

# Trim and reduce the image to limited colours
# - Shave off the edges to leave just the middle hourglass
# - Convert the colours down to just the palette we want to use
# - Make the white background transparent
# - Fill in the centre of the hourglass (by 'Close' the gaps, then trim to make sure we didn't cover
#   any of the outside edges), with a new colour (a light blue)
# - Put a border around the outside edge using the new colour (a light blue)
# - Ensure that the white background is transparent
# Note: The light blue becomes colour 1 in the output image, which we then make white when the hourglass is drawn.
for i in $( seq 0 59 ) ; do
    convert "${exclude_args[@]}" \
            frame_$i.png -shave 340x240 -gravity northeast -chop 2x2 \
            -resize ${width}x${height} +dither \
            -remap palette.ppm \
            -alpha on -fuzz 20% -transparent white -background white \
            \(  +clone \
                -bordercolor white -border 8x8 -transparent white \
                -channel A \
                    -morphology Close Disk:5.3 \
                    -morphology Erode Diamond \
                +channel \
                -shave 8x8 \
                +level-colors 'none,#addbe6' \
            \) -compose DstOver -composite \
            \(  +clone \
                -channel A -morphology EdgeOut Diamond +channel \
                -alpha remove -alpha off \
                +level-colors '#addbe6,white' \
                -alpha on -transparent white \
            \) -compose DstOver -composite \
            +repage simple_$i.png
done

# Convert the frames into a GIF to see what it would look like
ordered_images=( $( seq 36 59 ; echo 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ; seq 0 35 ) )
convert -delay 2 -dispose Background $(for i in ${ordered_images[*]} ; do echo -n "simple_$i.png " ; done) animated.gif

# Now convert the PNGs to shapes that we may be able to use in shape.py
index=0
translation=$(for col in "${generatedpalette[@]}" ; do echo " ; s/$col/c${index}c/g" ; index=$((index+1)) ; done)
cat > "${pyhourglass}" << EOM
# Hourglass shape

width = $width
height = $height
frameperiod = $frameperiod

palette = []
images = []

EOM

for pal in "${realpalette[@]}" ; do
    echo "palette.append(($(echo $pal | sed 's/ /, /g')))"
done >> "${pyhourglass}"
index=0
#echo "Translation: $translation"
for i in ${ordered_images[*]} ; do
    echo "images.append(("
    convert simple_$i.png ppm: \
        | pnmtopnm -plain \
        | sed -e "1,3 d; /^$/ d $translation ; s/c//g; s/ //g" \
        | perl -e '$in=join "", <STDIN>; $in =~ s/\n//g; for $row ($in =~ /(.{'$width'})/g) { print "        \"$row\",\n"; }'
    echo "    ))"
done >> "${pyhourglass}"
