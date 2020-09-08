#!/usr/bin/env python
"""
Make the data for a set of hourglass calls.

We take the shape.py data and we produce some code that can be used to use the hourglass.
"""

import pprint

import shape

# Number of bits per pixel
bpp = 2
# Number of pixels per word
ppw = 32 / bpp
def rowstring_to_words(rowstring):
    words = []
    word = 0
    for index, char in enumerate(rowstring):
        wordpixel = index & (ppw-1)
        word = word | (int(char) << (wordpixel * bpp))
        if wordpixel == (ppw-1) or index == len(rowstring) - 1:
            # This is the last pixel of the word, or the last pixel of the string
            # So we write into the array.
            words.append(word)
            word = 0

    return words


# Construct our unique row data.
# rows contains a mapping from the shape string to the index of the data for that row
# rowdata contains the actual data (at this point, not converted to words)
rows = {}
rowdata = []

# images_rowindexes will be constructed to contain a list of indexes into that rowdata
# for every row of every image.
images_rowindexes = []
for image in shape.images:
    imagerows = []
    for rowstring in image:
        if rowstring in image:
            if rowstring in rows:
                # This is a row we've seen before, so we can reuse it
                rowindex = rows[rowstring]
            else:
                # We've not seen this row before, so we will create a new entry for it
                rowindex = len(rowdata)
                rows[rowstring] = rowindex
                rowdata.append(rowstring)
            imagerows.append(rowindex)
    images_rowindexes.append(imagerows)


# Convert the string rowdata into words to write into memory
rowdata = [rowstring_to_words(rowstring) for rowstring in rowdata]

# Construct a list of deltas from the previous image - this is a list of tuples of (rownumber, rowindex)
# Strictly we could probably just store this data raw in memory and just reference it directly, or
# even copy the lot every time. But there's a certain amount of elegance in compacting the data in this
# way that I rather like.
deltas = []

# The first entry will always be a complete write of the image data, because it's the first frame -
# so we want to start with a clean slate each time.
deltas.append([(index, rowindex) for index, rowindex in enumerate(images_rowindexes[0])])

# Take a copy of the first image's state, so that we can track as calculate the deltas for each frame.
current_state = images_rowindexes[0][:]

# Now for each subsequent frame, we work out the deltas and store them into the array.
for rowindexes in images_rowindexes[1:]:
    image_deltas = []
    for index, rowindex in enumerate(rowindexes):
        if current_state[index] != rowindex:
            # This row differs from the previous frame, so we write its delta.
            image_deltas.append((index, rowindex))
            current_state[index] = rowindex
    deltas.append(image_deltas)

#pprint.pprint(images_rowindexes)
#pprint.pprint(rowdata)
#pprint.pprint(deltas[0])


def make_basic(rows, rowdata, deltas, images_rowindexes):
    # Write out a BASIC program that includes the data we wish to use:
    lines = []

    # Construct the rowdata
    wordsperrow = len(rowdata[0])
    nwords = wordsperrow * len(rowdata)
    # This algorithm only supports widths that are multiples of words
    lines.append("ON ERROR ERROR EXT ERR, REPORT$+\" at line \"+STR$ERL")
    lines.append(":")
    lines.append("COLOUR 128+7:CLS:COLOUR0")
    lines.append(":")
    lines.append("width% = {}".format((shape.width + 15) & ~15))
    lines.append("height% = {}".format(shape.height))
    lines.append("wordsperrow% = {}".format(wordsperrow))
    lines.append("nwords% = {}".format(nwords))
    lines.append("DIM rowdata% 4 * nwords%")
    lines.append("RESTORE +1")
    def basic_int(word):
        #if word & (1<<31):
        #    word = -(word - (1<<32))
        #    return '-&{:08x}'.format(word)
        return '&{:08x}'.format(word)

    for words in rowdata:
        words = [basic_int(word) for word in words]
        lines.append("DATA {}".format(', '.join(words)))
    lines.append("FOR n% = 0 TO nwords%-1")
    lines.append("  READ word%:rowdata%!(4 * n%) = word%")
    lines.append("NEXT")
    lines.append(":")

    # Set aside space for the frame references
    lines.append("nframes% = {}".format(len(deltas)))
    lines.append("DIM framedata% 8 * nframes%")
    lines.append(":")

    # Construct the list of deltas, and populate the frame references
    deltasize = sum(len(image_deltas) + 1 for image_deltas in deltas)
    lines.append("DIM deltas% 8*{}".format(deltasize))
    lines.append("")

    lines.append("deltaoffset% = 0")
    lines.append("RESTORE +1")
    lines.append("FOR frame% = 0 TO nframes%-1")
    lines.append(" framedata%!(frame% * 4) = deltaoffset%")
    lines.append(" REPEAT")
    lines.append("  READ rownumber%, rowindex%")
    # In theory this could be two halfwords, because the data is so small
    lines.append("  deltas%!(deltaoffset%) = rownumber%")
    lines.append("  deltas%!(deltaoffset%+4) = rowindex%")
    lines.append("  deltaoffset% += 8")
    lines.append(" UNTIL rownumber% = -1")
    lines.append("NEXT")
    lines.append(":")
    # Here's the actual delta data
    for index, image_deltas in enumerate(deltas):
        lines.append("REM Image {}".format(index))
        for rownumber, rowindex in image_deltas:
            lines.append("DATA {}, {}".format(rownumber, rowindex))
        lines.append("DATA {}, {}".format(-1, -1))
    lines.append(":")

    lines.append("DIM worddata% 10")
    lines.append("DIM pointerdata% 4 * wordsperrow% * height%")
    lines.append("worddata%?0 = 0:REM Define pointer shape")
    lines.append("worddata%?1 = 1:REM Shape number")
    lines.append("worddata%?2 = (width%*2+7)/8:REM Width in bytes")
    lines.append("worddata%?3 = height%:REM Height in rows")
    lines.append("worddata%?4 = width% / 2:REM Active point x")
    lines.append("worddata%?5 = height% / 2:REM Active point y")
    lines.append("worddata%!6 = pointerdata%")
    lines.append(":")

    lines.append("RESTORE + 1")
    lines.append("FOR col% = 0 TO {}".format(len(shape.palette)-1))
    lines.append(" READ colr%,colg%,colb%")
    lines.append(" VDU 19, col%, 25, colr%, colg%, colb%")
    lines.append("NEXT")
    for cols in shape.palette:
        lines.append("DATA {}".format(', '.join(str(col) for col in cols)))
    lines.append(":")


    # Select the pointer and turn it on
    lines.append("SYS \"OS_Byte\", 106, 1")
    lines.append(":")

    # Now we can step through the deltas for each frame.
    lines.append("framenum%=0")
    lines.append("WHILE TRUE")
    lines.append(" frame_deltas% = deltas% + framedata%!(framenum% * 4)")
    lines.append(" PRINT \"Frame \";framenum%")
    lines.append(" REPEAT")
    lines.append("  rownumber%=frame_deltas%!0:frame_deltas%+=4")
    lines.append("  rowindex%=frame_deltas%!0:frame_deltas%+=4")
    #lines.append("  PRINT \"  row \";rownumber%;\" => index \";rowindex%")
    lines.append("  IF rownumber% <> -1 THEN")
    # This would probably just be hardcoded for a specific case in a module - the whole point of using the
    # deltas is to not waste time, so looping is very wasteful.
    lines.append("   FORoffset%=0TOwordsperrow%*4-4 STEP 4")
    lines.append("    pointerdata%!(rownumber% * 4 * wordsperrow% + offset%) = rowdata%!(4 * wordsperrow% * rowindex% + offset%)")
    lines.append("   NEXT")
    lines.append("  ENDIF")
    lines.append(" UNTIL rownumber%=-1")
    lines.append(" SYS \"OS_Word\",21, worddata%")
    lines.append(" framenum% = (framenum% + 1) MOD nframes%")
    #lines.append(" G=GET:END")
    lines.append("  I=INKEY(2)")
    lines.append("ENDWHILE")

    with open("hourglass_basic,fd1", 'w') as fh:
        for line in lines:
            fh.write("{}\n".format(line))

make_basic(rows, rowdata, deltas, images_rowindexes)
