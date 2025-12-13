#!/usr/bin/env python3
"""
Make the data for a set of hourglass calls.

We take the shape.py data and we produce some code that can be used to use the hourglass.
"""

import os
import pprint
import sys

import percentage

# We want to use the 'shape.py' from the working directory
sys.path.append('.')

import shape

# Enable this to write the row data directly for each frame, rather than using
# a list of rowdata offsets.
# This is only efficient on memory if the rows are common between the different
# hourglass frames, otherwise it means that we're writing more data than we need
# in the module. But is that really an issue?
# Turns out that it is - the fact that a row isn't (usually 2 words) and we have
# to spend an extra word to reference it means that you need to have a lot of
# duplicated rows to make these references to rows efficient.
# Sadly I've optimised for a case that isn't likely, or even possible, on
# RISC OS Classic. As such, the direct_rowdata is left on.
# If you were to have a repetative hourglass which was wider than 2 words,
# you might turn this off again, but it doesn't offer any benefit right now.
direct_rowdata = True

# Percentage parameters
percentage_digits_file = getattr(shape, 'percentage_digits_file', 'digits.json')
percentage_vspace = getattr(shape, 'percentage_vspace', 1)
percentage_bar_enabled = getattr(shape, 'percentage_bar_enabled', True)
percentage_bar_height = getattr(shape, 'percentage_bar_height', 7)
percentage_bar_bgcolour = getattr(shape, 'percentage_bar_bgcolour', 2)
percentage_bgcolour = getattr(shape, 'percentage_bgcolour', 0)
percentage_digits_enabled = getattr(shape, 'percentage_digits_enabled', True)
percentage_digits_border = getattr(shape, 'percentage_digits_border', 1)
percentage_digits_bgcolour = getattr(shape, 'percentage_digits_bgcolour', 2)
percentage_bar_hspace = getattr(shape, 'percentage_bar_hspace', 2)
percentage_inset = getattr(shape, 'percentage_inset', 0)



# Number of bits per pixel
bpp = 2
# Number of pixels per word
ppw = int(32 / bpp)
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

# Take a copy of the first image's state, so that we can calculate the deltas for each frame.
current_state = images_rowindexes[0][:]

# Now for each subsequent frame, we work out the deltas and store them into the array.
print("Calculating the frame deltas (%i rows)" % (len(current_state),))
for rowindexes in images_rowindexes[1:]:
    #print("New frame")
    image_deltas = []
    for index, rowindex in enumerate(rowindexes):
        #print("  check row %i" % (index,))
        if current_state[index] != rowindex:
            #print("  row %i differs, writing delta" % (index,))
            # This row differs from the previous frame, so we write its delta.
            image_deltas.append((index, rowindex))
            current_state[index] = rowindex
    deltas.append(image_deltas)

#pprint.pprint(images_rowindexes)
#pprint.pprint(rowdata)
#pprint.pprint(deltas[0])


# Construct the bitmap data for the percentages
# (try the current directory first, then fall back to the makehourglass.py directory)
digits_file = percentage_digits_file
if not os.path.isfile(digits_file):
    digits_file = os.path.join(os.path.dirname(__file__), digits_file)
space = shape.width - percentage_inset * 2
bar_width = 0

percentage_height = 0
if percentage_digits_enabled:
    percentage_chars = percentage.Characters(digits_file)
    # The digits might be "99%"
    space -= percentage_chars.width * 3
    space -= percentage_digits_border * 2
if percentage_bar_enabled:
    if percentage_digits_enabled:
        space -= percentage_bar_hspace
    bar_width = space if space > 0 else 0

if percentage_bar_enabled or percentage_digits_enabled:
    percentage_bitmaps = []
    percentage_worddata = []
    bar = percentage.ProgressBar(bar_width, percentage_bar_height, fill=percentage_bar_bgcolour)
    for pct in range(0, 100):
        bm = percentage.Bitmap(0, 0)
        if percentage_bar_enabled:
            bar_bm = bar.bitmap(pct)
            if percentage_digits_enabled:
                bar_bm.append_columns(percentage_bar_hspace)
            bm.append(bar_bm)
        else:
            percentage_bm = percentage.Bitmap(0, 0)
            bm.append(percentage_bm)

        if percentage_digits_enabled:
            pad = ''
            if percentage_bar_enabled:
                if pct < 10:
                    pad = ' '
            percentage_bm = percentage_chars.bitmap('{}%{}'.format(pct, pad), fg=3, bg=percentage_digits_bgcolour)
            percentage_bm.border(size=percentage_digits_border, colour=percentage_digits_bgcolour)
            #pprint.pprint(percentage_bm.grid)
            bm.append(percentage_bm, align=0)

        bm.set_width(width=shape.width - percentage_inset * 2, align=0)
        bm.replace(0, percentage_bgcolour)
        bm.set_width(width=shape.width, align=0)
        bm.append_rows(rows=percentage_vspace, top=True)

        percentage_bitmaps.append(bm)
        percentage_worddata.append(bm.word_data())
        percentage_height = bm.height

    # Now let's see if we can reduce the frame data by finding common bitmaps
    # This is only going to work out efficiently for the percentage alone - the
    # digits will all be different, but oh well.
    percentage_offset = 0
    percentage_offsets = []
    percentage_worddata_size = 4 * len(percentage_worddata[0]) * len(percentage_worddata[0][0])
    for pct in range(0, 100):
        # Look at all the preceding words, to see if we can find a block that's the same
        seen_percentage_offset = None
        for prior_pct in range(pct):
            if percentage_worddata[pct] == percentage_worddata[prior_pct]:
                seen_percentage_offset = percentage_offsets[prior_pct]
                break
        if seen_percentage_offset is None:
            percentage_offsets.append(percentage_offset)
            percentage_offset += percentage_worddata_size
            #pprint.pprint(percentage_bitmaps[pct].grid)
        else:
            percentage_offsets.append(seen_percentage_offset)
            percentage_worddata[pct] = None


# Auto-disable if it wouldn't work.
if shape.height + percentage_height > 32:
    # Everything is keyed off percentage_height
    percentage_height = 0


def make_python(filename):
    """
    Write out a Python fragment to defind the content of the hourglass.
    """
    lines = []
    def python_int(word):
        #if word & (1<<31):
        #    word = -(word - (1<<32))
        #    return '-&{:08x}'.format(word)
        return '0x{:08x}'.format(word)

    lines.append("class HourglassData(object):")
    lines.append('    """')
    lines.append('    Container holding data for the Hourglass.')
    lines.append('    """')
    lines.append("    period_cs = {}".format(shape.frameperiod))
    lines.append("    active_x = {}".format(shape.activex))
    lines.append("    active_y = {}".format(shape.activey))
    lines.append("")
    lines.append("    palette = [")
    for r, g, b in shape.palette[1:]:
        lines.append("            ({}, {}, {}),".format(r, g, b))
    lines.append("        ]")
    lines.append("")
    lines.append("    width = {}".format((shape.width + 15) & ~15))
    lines.append("    height = {}".format(shape.height))
    lines.append("    frames = [")

    for index, image in enumerate(shape.images):
        imagerows = []
        lines.append("        [")
        lines.append("            # frame {}".format(index))
        for rowstring in image:
            words = rowstring_to_words(rowstring)
            words = [python_int(word) for word in words]
            lines.append("            {},".format(', '.join(words)))
        lines.append("        ],")

    lines.append("    ]")

    lines.append("    percentage_height = {}".format(percentage_height))
    if percentage_height:
        lines.append("    percentage_worddata_size = {}".format(percentage_worddata_size))
        lines.append("    percentages = {")
        index_lookup = dict((v, pct) for (pct, v) in enumerate(percentage_offsets) if percentage_worddata[pct] is not None)
        last_index = -1
        for index, image in enumerate(percentage_worddata):
            if image:
                lines.append("        {}: [".format(index))
                for words in image:
                    words = [python_int(word) for word in words]
                    lines.append("            {},".format(', '.join(words)))
                lines.append("        ],")
            else:
                # This is a duplicate of...
                lines.append("        {}: {},".format(index, index_lookup[percentage_offsets[index]]))
        lines.append("    }")
    else:
        lines.append("    percentage_worddata_size = 0")

    if sys.platform == 'riscos':
        filename = filename[:-3] + '/py'
    with open(filename, 'w') as fh:
        for line in lines:
            fh.write("{}\n".format(line))


def make_basic(rows, rowdata, deltas, images_rowindexes, filename):
    """
    Write out a BASIC program that includes the data we wish to use.
    """
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
    lines.append("active_x% = {}".format(shape.activex))
    lines.append("active_y% = {}".format(shape.activey))
    lines.append("period% = {}".format(shape.frameperiod))
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
    lines.append("worddata%?4 = active_x%")
    lines.append("worddata%?5 = active_y%")
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
    lines.append("  I=INKEY(period%)")
    lines.append("ENDWHILE")

    if sys.platform != 'riscos':
        filename += ',fd1'
    with open(filename, 'w') as fh:
        for line in lines:
            fh.write("{}\n".format(line))
    if sys.platform == 'riscos':
        # FIXME: On RISC OS set the filetype
        pass


def make_objasm(rows, rowdata, deltas, images_rowindexes,filename):
    # Write out an objasm function to allow us to run the hourglass,
    # and the C header that lets us use it
    lines = []
    hlines = []

    # Header for the H file
    hlines.append("#ifndef HOURGLASS_ASM_H")
    hlines.append("#define HOURGLASS_ASM_H")
    hlines.append("")
    hlines.append("typedef void *hourglass_workspace_t;")

    # Construct the rowdata
    wordsperrow = len(rowdata[0])
    nwords = wordsperrow * len(rowdata)
    # This algorithm only supports widths that are multiples of words
    lines.append("          AREA |C$$code|, CODE, READONLY")
    lines.append("")
    lines.append("; constants")
    lines.append("width             * {}".format((shape.width + 15) & ~15))
    lines.append("height            * {}".format(shape.height))
    lines.append("period            * {}".format(shape.frameperiod))
    lines.append("wordsperrow       * {}".format(wordsperrow))
    lines.append("nwords            * {}".format(nwords))
    lines.append("nframes           * {}".format(len(deltas)))
    lines.append("active_x          * {}".format(shape.activex))
    lines.append("active_y          * {}".format(shape.activey))
    lines.append("percentage_height        * {}".format(percentage_height))
    if percentage_height:
        lines.append("percentage_worddata_size * {}".format(percentage_worddata_size))
    lines.append("")
    lines.append("; Workspace for changing the hourglass rendition")
    lines.append("                  ^ 0, r12")
    lines.append("hg_framenum       # 4                         ; frame number")
    lines.append("hg_percentage     # 4                         ; percentage to show")
    lines.append("hg_percentagenow  # 4                         ; percentage being shown")
    lines.append("hg_leds           # 4                         ; LED flags (N/I)")
    lines.append("hg_oldpointer     # 4                         ; Old pointer configuration")
    lines.append("hg_oldcolours     # 4 * 3                     ; Old palette entries")
    lines.append("hg_word           # 12                        ; OS_Word block")
    lines.append("hg_currentdata    # 4 * wordsperrow * (height + percentage_height)  ; Current data for the hourglass")
    lines.append("hg_workspacesize  * :INDEX: @                 ; Size of this workspace")
    lines.append("")
    lines.append("; SWI numbers")
    lines.append("XOS_Byte          * 0x20006")
    lines.append("XOS_Word          * 0x20007")
    lines.append("XOS_ReadPalette   * 0x2002F")
    lines.append("")

    lines.append('; -------------------------------------------------')
    lines.append('        MACRO')
    lines.append('$label  SIGNATURE')
    lines.append('        ALIGN   4')
    lines.append('        =       "$label",0')
    lines.append('        ALIGN   4')
    lines.append('        DCD     &FF000000+(:LEN:"$label"+4):AND::NOT:3')
    lines.append('$label')
    lines.append('        MEND')
    lines.append('')

    if not direct_rowdata:
        lines.append("; Data for the rows of the hourglass")
        lines.append("rowdata")
        for words in rowdata:
            words = ['&{:08x}'.format(word) for word in words]
            lines.append("          DCD     {}".format(', '.join(words)))

    framedelta_offsets = []
    deltaoffset = 0

    lines.append("")
    lines.append("; Data for deltas between frames")
    lines.append("deltas")
    # Here's the actual delta data
    for index, image_deltas in enumerate(deltas):
        framedelta_offsets.append(deltaoffset)
        lines.append("          ; frame {}".format(index))
        for rownumber, rowindex in image_deltas:
            # We actually write the offset into the hg_currentdata, and the offset into the rowdata
            # This means that we don't need to calculate these values at runtime.
            if direct_rowdata:
                words = [rownumber * wordsperrow * 4]
                words.extend(rowdata[rowindex])
                lines.append("          DCD     {}".format(', '.join('&{:08x}'.format(word) for word in words)))
                deltaoffset += 4 * len(words)
            else:
                lines.append("          DCD     {}, {}".format(rownumber * wordsperrow * 4,
                                                               rowindex * wordsperrow * 4))
                deltaoffset += 8
        lines.append("          DCD     {}".format(-1))
        deltaoffset += 4

    lines.append("")
    lines.append("; Offsets into the deltas for each frame")
    lines.append("frame_deltas")
    for index, offset in enumerate(framedelta_offsets):
        lines.append("          DCD     {}  ; frame {}".format(offset, index))

    # Now the data for the percentage
    if percentage_height:
        lines.append("")
        lines.append("; Offsets into the data for each percentage line")
        lines.append("percentage_offsets")
        for index, offset in enumerate(percentage_offsets):
            lines.append("          DCD     {}  ; {}%".format(offset, index))

        lines.append("")
        lines.append("; Data for the rows to append for the percentage")
        lines.append("percentage_data")
        for index, rowdata in enumerate(percentage_worddata):
            if rowdata is None:
                continue
            lines.append("          ; {}%".format(index))
            for rowindex, words in enumerate(rowdata):
                lines.append("          DCD     {}".format(', '.join('&{:08x}'.format(word) for word in words)))


    lines.append("")
    lines.append("; Palette data")
    lines.append("palette")
    # We skip the 0 entry, because colour 0 is transparent
    for r, g, b in shape.palette[1:]:
        lines.append("          DCB     {}, {}, {}".format(r, g, b))
    lines.append("          ALIGN")

    lines.append("")
    lines.append("; Read the period between frames")
    lines.append("; <=  R0 = cs between frames")
    hlines.append("int hourglass_getframeperiod(void);")
    lines.append("hourglass_getframeperiod SIGNATURE")
    lines.append("          EXPORT  hourglass_getframeperiod")
    lines.append("          MOV     r0, #period")
    lines.append("          MOV     pc, lr")
    lines.append("")

    lines.append("")
    lines.append("; Read the size of the workspace block")
    lines.append("; <=  R0 = size of hourglass workspace")
    hlines.append("int hourglass_getwssize(void);")
    lines.append("hourglass_getwssize SIGNATURE")
    lines.append("          EXPORT  hourglass_getwssize")
    lines.append("          MOV     r0, #hg_workspacesize")
    lines.append("          MOV     pc, lr")
    lines.append("")
    lines.append("; Initialisation function")
    lines.append("; =>  R0 = hourglass workspace")
    hlines.append("void hourglass_init(hourglass_workspace_t *ws);")
    lines.append("hourglass_init SIGNATURE")
    lines.append("          EXPORT  hourglass_init")
    lines.append("          MOV     r12, r0")
    lines.append("          MOV     r0, #0")
    lines.append("          STR     r0, hg_framenum")
    lines.append("          STR     r0, hg_leds")
    lines.append("          MOV     r0, #-1")
    lines.append("          STR     r0, hg_percentagenow")
    lines.append("          MOV     r0, #100")
    lines.append("          STR     r0, hg_percentage")
    lines.append("          LDR     r0, wordblock_0")
    lines.append("          STR     r0, hg_word")
    lines.append("          LDR     r0, wordblock_4")
    lines.append("          ADR     r1, hg_currentdata")
    lines.append("          ORR     r0, r0, r1, LSL #16         ; assign the low half word of pointer data")
    lines.append("          STR     r0, hg_word + 4")
    lines.append("          MOV     r0, r1, LSR #16             ; and the high half word")
    lines.append("          STR     r0, hg_word + 8")
    lines.append("; no need to initialise the currentdata; it will be updated by the first frame")
    lines.append("          MOV     pc, lr")
    lines.append("")

    lines.append("wordblock_0")
    lines.append("          DCB     0                           ; define pointer shape")
    lines.append("          DCB     3                           ; shape number (will toggle 3-4)")
    lines.append("          DCB     (width*2+7)/8               ; width in bytes")
    lines.append("          DCB     height                      ; height")
    lines.append("wordblock_4")
    lines.append("          DCB     active_x                    ; active x offset")
    lines.append("          DCB     active_y                    ; active y offset")
    lines.append("          DCB     0                           ; b0-7 of the address of the pointer data")
    lines.append("          DCB     0                           ; b8-15 of address of the pointer data")

    lines.append("")
    lines.append("; Start the hourglass")
    lines.append("; =>  R0 = hourglass workspace")
    hlines.append("void hourglass_start(hourglass_workspace_t *ws);")
    lines.append("hourglass_start SIGNATURE")
    lines.append("          EXPORT  hourglass_start")
    lines.append("          STMFD   sp!, {r4, r5, lr}")
    lines.append("          SUB     sp, sp, #8")
    lines.append("          MOV     r12, r0")
    lines.append("          MOV     r0, #0")
    lines.append("          STR     r0, hg_framenum")
    lines.append("          MOV     r0, #1")
    lines.append("          MOV     r1, #25                     ; read pointer colour 1")
    lines.append("          SWI     XOS_ReadPalette")
    lines.append("          LDRVS   r2, =&81397900              ; purple if it wasn't set")
    lines.append("          STR     r2, hg_oldcolours + 4 * 0")
    lines.append("          MOV     r0, #2")
    lines.append("          MOV     r1, #25                     ; read pointer colour 2")
    lines.append("          SWI     XOS_ReadPalette")
    lines.append("          LDRVS   r2, =&66FFFF00              ; yellow if it wasn't set")
    lines.append("          STR     r2, hg_oldcolours + 4 * 1")
    lines.append("          MOV     r0, #3")
    lines.append("          MOV     r1, #25                     ; read pointer colour 3")
    lines.append("          SWI     XOS_ReadPalette")
    lines.append("          LDRVS   r2, =&00000000              ; black if it wasn't set")
    lines.append("          STR     r2, hg_oldcolours + 4 * 2")
    lines.append("; now set the palette up for our hourglass")
    lines.append("          MOV     r1, sp")
    lines.append("          ADRL    r2, palette")
    for colour_number in range(len(shape.palette) - 1):
        lines.append("; colour {}".format(colour_number + 1))
        lines.append("          MOV     r0, #{}".format(colour_number + 1))
        lines.append("          STRB    r0, [r1, #0]")
        lines.append("          MOV     r0, #25                     ; set pointer colour 1")
        lines.append("          STRB    r0, [r1, #1]")
        lines.append("          LDRB    r0, [r2], #1")
        lines.append("          STRB    r0, [r1, #2]                ; red")
        lines.append("          LDRB    r0, [r2], #1")
        lines.append("          STRB    r0, [r1, #3]                ; green")
        lines.append("          LDRB    r0, [r2], #1")
        lines.append("          STRB    r0, [r1, #4]                ; blue")
        lines.append("          MOV     r0, #12")
        lines.append("          SWI     XOS_Word                    ; Set palette")

    lines.append("          MOV     r1, #127                        ; invalid pointer number to read the pointer")
    lines.append("          MOV     r0, #106                        ; select pointer")
    lines.append("          SWI     XOS_Byte")
    lines.append("          MOVVS   r1, #0                          ; if there was an error, turn off")
    lines.append("          STR     r1, hg_oldpointer")

    lines.append("          ADD     sp, sp, #8")
    lines.append("          LDMFD   sp!, {r4, r5, lr}")
    lines.append("          MOV     r0, r12")
    lines.append("          B       hourglass_frame                 ; exit via the first frame")

    lines.append("")
    lines.append("; Stop the hourglass")
    lines.append("; =>  R0 = hourglass workspace")
    hlines.append("void hourglass_stop(hourglass_workspace_t *ws);")
    lines.append("hourglass_stop SIGNATURE")
    lines.append("          EXPORT  hourglass_stop")
    lines.append("          STMFD   sp!, {r4, r5, lr}")
    lines.append("          SUB     sp, sp, #8")
    lines.append("          MOV     r12, r0")

    lines.append("          MOV     r0, #-1")
    lines.append("          STR     r0, hg_percentagenow")
    lines.append("          MOV     r0, #100")
    lines.append("          STR     r0, hg_percentage")

    lines.append("          LDR     r4, hg_oldpointer               ; work out the old pointer shape")
    lines.append("          BIC     r4, r4, #127                    ; turn off the pointer whilst we change colours")
    lines.append("          MOV     r0, #106                        ; select pointer")
    lines.append("          SWI     XOS_Byte")

    lines.append("; restore the palette up for old pointer")
    lines.append("          MOV     r1, sp")
    for colour_number in range(len(shape.palette) - 1):
        lines.append("; colour {}".format(colour_number + 1))
        lines.append("          ADR     r2, hg_oldcolours + 4 * {} + 1".format(colour_number))
        lines.append("          MOV     r0, #{}".format(colour_number + 1))
        lines.append("          STRB    r0, [r1, #0]")
        lines.append("          MOV     r0, #25                         ; set pointer colour 1")
        lines.append("          STRB    r0, [r1, #1]")
        lines.append("          LDRB    r0, [r2], #1")
        lines.append("          STRB    r0, [r1, #2]                    ; red")
        lines.append("          LDRB    r0, [r2], #1")
        lines.append("          STRB    r0, [r1, #3]                    ; green")
        lines.append("          LDRB    r0, [r2], #1")
        lines.append("          STRB    r0, [r1, #4]                    ; blue")
        lines.append("          MOV     r0, #12")
        lines.append("          SWI     XOS_Word                        ; Set palette")

    lines.append("          MOV     r1, r4                          ; re-select the old pointer number")
    lines.append("          MOV     r0, #106                        ; select pointer")
    lines.append("          SWI     XOS_Byte")

    lines.append("          ADD     sp, sp, #8")
    lines.append("          LDMFD   sp!, {r4, r5, pc}")

    lines.append("")
    lines.append("; Frame update - sets the hourglass shape for the current frame")
    lines.append("; =>  R0 = hourglass workspace")
    hlines.append("void hourglass_frame(hourglass_workspace_t *ws);")
    lines.append("hourglass_frame SIGNATURE")
    lines.append("          EXPORT  hourglass_frame")
    lines.append("          STMFD   sp!, {r4, r5, lr}")
    lines.append("          MOV     r12, r0")
    lines.append("          LDR     r0, hg_framenum")
    lines.append("          ADRL    r1, frame_deltas")
    lines.append("          LDR     r0, [r1, r0, LSL #2]            ; offset within deltas for this frame")
    lines.append("          ADRL    r1, deltas")
    lines.append("          ADD     r1, r1, r0")
    if not direct_rowdata:
        lines.append("          ADRL    r2, rowdata")
    lines.append("          ADRL    r5, hg_currentdata")
    lines.append("rowloop")
    if direct_rowdata:
        lines.append("          LDR     r3, [r1], #4                    ; r3 = currentdata offset")
        lines.append("          CMP     r3, #-1                         ; end of the rows")
        lines.append("          BEQ     rowend")

        lines.append("      [ wordsperrow = 1")
        lines.append("          LDR     r0, [r1], #4                    ; read a word")
        lines.append("          STR     r0, [r3, r5]                    ; store into the currentdata")
        lines.append("      ]")
        lines.append("      [ wordsperrow = 2")
        lines.append("          LDMIA   r1!, {r0, r2}                   ; read two word from rowdata")
        lines.append("          STR     r0, [r3, r5]!                   ; store into the currentdata")
        lines.append("          STR     r2, [r3, #4]                    ; store into the currentdata")
        lines.append("      ]")
        lines.append("      [ wordsperrow = 3")
        lines.append("          LDMIA   r1!, {r0, r2, r4}               ; read a word from rowdata")
        lines.append("          ADD     r3, r3, r5                      ; work out the line offset")
        lines.append("          STMIA   r3!, {r0, r2, r4}               ; store into the currentdata")
        lines.append("      ]")
        lines.append("      [ wordsperrow = 4")
        lines.append("          LDMIA   r1!, {r0, r2, r4, lr}           ; read a word from rowdata")
        lines.append("          ADD     r3, r3, r5                      ; work out the line offset")
        lines.append("          STMIA   r3!, {r0, r2, r4, lr}           ; store into the currentdata")
        lines.append("      ]")
    else:
        lines.append("          LDMIA   r1!, {r3, r4}                   ; r3 = currentdata offset, r4 = row data offset")
        lines.append("          CMP     r3, #-1                         ; end of the rows")
        lines.append("          BEQ     rowend")

        lines.append("          LDR     r0, [r4, r2]!                   ; read a word from rowdata")
        lines.append("          STR     r0, [r3, r5]!                   ; store into the currentdata")

        # FIXME: Remember how you do a loop in objasm, cos this could be pretty simple - alternatively use a
        #        LDMIA?
        lines.append("      [ wordsperrow > 1")
        lines.append("          LDR     r0, [r4, #4]!                   ; read a word from rowdata")
        lines.append("          STR     r0, [r3, #4]!                   ; store into the currentdata")
        lines.append("      ]")
        lines.append("      [ wordsperrow > 2")
        lines.append("          LDR     r0, [r4, #4]!                   ; read a word from rowdata")
        lines.append("          STR     r0, [r3, #4]!                   ; store into the currentdata")
        lines.append("      ]")
        lines.append("      [ wordsperrow > 3")
        lines.append("          LDR     r0, [r4, #4]!                   ; read a word from rowdata")
        lines.append("          STR     r0, [r3, #4]!                   ; store into the currentdata")
        lines.append("      ]")
    lines.append("          B       rowloop")
    lines.append("")

    lines.append("rowend")
    # Decide whether we need to handle the percentage we're going to show
    if percentage_height:
        lines.append("          LDR     r14, hg_percentage")
        lines.append("          LDR     r0, hg_percentagenow")
        lines.append("          TEQ     r0, r14")
        lines.append("          BEQ     percentage_up_to_date")
        lines.append("")
        lines.append("          TEQ     r14, #100")
        lines.append("          MOVEQ   r0, #height")
        lines.append("          MOVNE   r0, #height + percentage_height")
        lines.append("          STRB    r0, hg_word + 3                 ; update pointer height for percentage block")
        lines.append("          STR     r14, hg_percentagenow")
        lines.append("          BEQ     percentage_up_to_date")
        lines.append("")
        lines.append("          ADRL    r1, percentage_offsets")
        lines.append("          LDR     r0, [r1, r14, LSL #2]           ; offset within percentage data")
        lines.append("          ADRL    r1, percentage_data")
        lines.append("          ADD     r1, r1, r0")

        lines.append("          ADD     r3, r5, #wordsperrow * 4 * height ; move to the end of the frame data")
        lines.append("          GBLA    worddata_to_copy")
        lines.append("worddata_to_copy SETA percentage_worddata_size")
        lines.append("          WHILE   worddata_to_copy > 4 * 4")
        lines.append("          LDMIA   r1!, {r0, r2, r4, lr}           ; read a word from rowdata")
        lines.append("          STMIA   r3!, {r0, r2, r4, lr}           ; store into the currentdata")
        lines.append("worddata_to_copy SETA worddata_to_copy - 4 * 4")
        lines.append("          WEND")
        lines.append("          WHILE   worddata_to_copy > 0")
        lines.append("          LDR     r0, [r1], #4                    ; read trailing word")
        lines.append("          STR     r0, [r3], #4                    ; store trailing word")
        lines.append("worddata_to_copy SETA worddata_to_copy - 4")
        lines.append("          WEND")
        lines.append("")
        lines.append("percentage_up_to_date")

    lines.append("          MOV     r0, #21                         ; Set Pointer parameters")
    lines.append("          ADR     r1, hg_word")
    lines.append("          SWI     XOS_Word")

    # It'd be better if we changed the pointer shape when we got the next VSync, but I'm being lazy.
    lines.append("")
    lines.append("          LDRB    r1, hg_word + 1                 ; get the hourglass pointer number we will use")
    lines.append("          RSB     lr, r1, #7                      ; toggles 3 to 4")
    lines.append("          STRB    lr, hg_word + 1                 ; toggles the pointer number we use next time")
    lines.append("          MOV     r0, #106                        ; select pointer")
    lines.append("          SWI     XOS_Byte")

    lines.append("")
    lines.append("          LDR     r0, hg_framenum")
    lines.append("          ADD     r0, r0, #1")
    lines.append("          TEQ     r0, #nframes")
    lines.append("          MOVEQ   r0, #0                          ; reset counter; we've cycled")
    lines.append("          STR     r0, hg_framenum")

    lines.append("          LDMFD   sp!, {r4, r5, pc}")

    lines.append("")
    lines.append("; Frame update within an IRQ")
    lines.append("; =>  R12 = hourglass workspace")
    hlines.append("void hourglass_frame_irq(void);")
    lines.append("hourglass_frame_irq SIGNATURE")
    lines.append("          EXPORT  hourglass_frame_irq")
    lines.append("          STMFD   sp!, {r0-r3, r4, r5, r12, lr}")
    lines.append("          MOV     r0, r12")
    lines.append("          MRS     r4, CPSR")
    lines.append("          BIC     r1, r4, #&F")
    lines.append("          ORR     r1, r1, #&3")
    lines.append("          MSR     CPSR_csxf, r1                    ; Enter SVC mode (keep bitness)")

    lines.append("          MOV     r5, lr")
    lines.append("          BL      hourglass_frame")
    lines.append("          MOV     lr, r5")

    lines.append("          MSR     CPSR_cxsf, r4                    ; Restore the mode")
    lines.append("          LDMFD   sp!, {r0-r3, r4, r5, r12, pc}")

    lines.append("")
    lines.append("; Set the percentage of the hourglass")
    lines.append("; =>  R0 = hourglass workspace")
    lines.append(";     R1 = percentage (0-99, or 100 to turn the percentage off)")
    hlines.append("void hourglass_percentage(hourglass_workspace_t *ws, int percentage);")
    lines.append("hourglass_percentage SIGNATURE")
    lines.append("          STMFD   sp!, {r4, r5, lr}")
    lines.append("          EXPORT  hourglass_percentage")
    lines.append("          MOV     r12, r0")
    lines.append("          STR     r1, hg_percentage")
    lines.append("          LDMFD   sp!, {r4, r5, pc}")


    lines.append("")
    lines.append("          END")

    # Trailer for the H file
    hlines.append("")
    hlines.append("#endif /* HOURGLASS_ASM_H */")

    # Actually we'll build two files - one for the assembler s file, and one for the header
    if not os.path.isdir('s'):
        os.mkdir('s')
    sfilename = os.path.join('s', filename)
    with open(sfilename, 'w') as fh:
        for line in lines:
            fh.write("{}\n".format(line))

    if not os.path.isdir('h'):
        os.mkdir('h')
    hfilename = os.path.join('h', filename)
    with open(hfilename, 'w') as fh:
        for line in hlines:
            fh.write("{}\n".format(line))


make_basic(rows, rowdata, deltas, images_rowindexes, filename='hourglass_basic')
make_python(filename='hourglass_frames.py')
make_objasm(rows, rowdata, deltas, images_rowindexes, filename='asm')
