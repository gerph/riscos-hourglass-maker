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

# RISC OS Classic cannot have icons larger than 32 pixels wide.
width=32
height=32

# Period between frames in centiseconds
frameperiod=2

# The palette to use for processing - just a black (and maybe a grey)
#palette=("255 255 255" "0 0 0" "128 128 128" "64 64 64")
palette=("255 255 255" "0 0 0")

# The palette to use for the actual hourglass
realpalette=("${palette[@]}")
realpalette=("255 255 255" "64 64 192")

# Generate the palette to use
cat > palette.ppm <<EOM
P3
# Blue palette
${#palette[@]} 1
255
${palette[*]}
EOM

# Trim and reduce the image to limited colours
for i in $( seq 0 59 ) ; do
    convert "${exclude_args[@]}" \
            frame_$i.png -shave 340x240 -gravity northeast -chop 2x2 \
            -resize ${width}x${height} +dither \
            -remap palette.ppm \
            -alpha on -fuzz 20% -transparent white -background white \
            +repage simple_$i.png

done

# Convert the frames into a GIF to see what it would look like
ordered_images=( $( seq 36 59 ; echo 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ; seq 0 35 ) )
convert -delay 2 -dispose Background $(for i in ${ordered_images[*]} ; do echo -n "simple_$i.png " ; done) animated.gif

# Now convert the PNGs to shapes that we may be able to use in shape.py
index=0
translation=$(for col in "${palette[@]}" ; do echo " ; s/$col/c${index}c/g" ; index=$((index+1)) ; done)
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
