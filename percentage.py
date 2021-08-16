"""
Digit data for the hourglass.
"""

import os
import json


class Bitmap(object):

    def __init__(self, width, height, bg=' '):
        self.width = width
        self.bg = (str(bg) + ' ')[:1] if bg else ' '
        self.grid = [self.bg * self.width] * height

    @property
    def height(self):
        return len(self.grid)

    def copy(self):
        new_bm = self.__class__(self.width, self.height, bg=self.bg)
        new_bm.grid = self.grid[:]
        return new_bm

    def set_bg(self, colour=None):
        self.bg = (str(colour) + ' ')[:1] if colour else ' '

    def hline(self, colour, y, x, x1=None, width=None):
        colour = (str(colour) + ' ')[:1]
        if width is None:
            width = x1 - x
        line = self.grid[y]
        line = line[:x] + (colour * width) + line[x + width:]
        self.grid[y] = line

    def vline(self, colour, x, y, y1=None, height=None):
        colour = str(colour)[:1] or self.bg
        if height is None:
            if y1 < y:
                (y, y1) = (y1, y)
            height = abs(y1 - y)

        for y in range(y, y + height):
            line = self.grid[y]
            line = line[:x] + colour + line[x + 1:]
            self.grid[y] = line

    def replace(self, old_colour, new_colour):
        old_colour = str(old_colour)[:1]
        if old_colour == '0':
            old_colour = ' '
        new_colour = str(new_colour)[:1]
        for y in range(0, self.height):
            self.grid[y] = self.grid[y].replace(old_colour, new_colour)
            if old_colour == ' ':
                self.grid[y] = self.grid[y].replace('0', new_colour)

    def append_rows(self, rows=1, top=False):
        """
        Append rows at the top or bottom.
        """
        row = self.bg * self.width
        for _ in range(rows):
            if top:
                self.grid.insert(0, row)
            else:
                self.grid.append(row)

    def append_columns(self, columns=1):
        """
        Append columns on the right.
        """
        more = self.bg * columns
        for y, row in enumerate(self.grid):
            self.grid[y] = row + more
        self.width += columns

    def border(self, size=1, colour=None):
        if size == 0:
            return

        if colour is None:
            colour = self.bg
        else:
            colour = str(colour)

        # Add the space to the left and the right
        more = colour * size
        for y, row in enumerate(self.grid):
            self.grid[y] = more + row + more
        self.width += size * 2

        # Now add new rows at the start and end
        blank = colour * self.width
        for _ in range(size):
            self.grid.insert(0, blank)
            self.grid.append(blank)

    def set_width(self, width, align=0, colour=None):
        diff = width - self.width
        if align == 0:
            # Center
            pad_left = int(diff) / 2
            pad_right = diff - pad_left
        elif align < 0:
            # Left align
            pad_left = 0
            pad_right = diff
        else:
            # Right align
            pad_left = diff
            pad_right = 0

        if diff < 0:
            for y, row in enumerate(self.grid):
                if pad_right != 0:
                    self.grid[y] = row[-pad_left:pad_right]
                else:
                    self.grid[y] = row[-pad_left:]
        else:
            str_left = ' ' * pad_left
            str_right = ' ' * pad_right
            for y, row in enumerate(self.grid):
                self.grid[y] = ''.join((str_left, row, str_right))
        self.width += diff

    def append(self, bitmap, align=0):
        """
        Append a bitmap to the one we have.

        @param bitmap:  the bitmap to add
        @param align:   alignment, 0 => center, -1 => top, 1 => bottom
        """
        if bitmap.height > self.height:
            # The one we're adding is taller, so let's add some pad lines to the top and bottom
            if align < 0:
                pad_top = 0
            else:
                if align == 0:
                    pad_top = int((bitmap.height - self.height) / 2)
                else:
                    pad_top = bitmap.height - self.height
                for _ in range(pad_top):
                    self.grid.insert(0, self.bg * self.width)

            while self.height < bitmap.height:
                self.grid.append(self.bg * self.width)

        if align < 0:
            y0 = 0
        elif align == 0:
            y0 = int((self.height - bitmap.height) / 2)
        else:
            y0 = self.height - bitmap.height

        for yoffset, row in enumerate(bitmap.grid):
            self.grid[y0 + yoffset] += row

        # Now balance any addition lines we need to
        new_width = self.width + bitmap.width
        for y, row in enumerate(self.grid):
            if len(row) < new_width:
                self.grid[y] = row + (self.bg * (new_width - len(row)))
        self.width = new_width

    def word_data(self):
        """
        Return the word data as might be used by RISC OS.
        """
        data = []
        import sys
        for row in self.grid:
            rowdata = []
            word = 0
            for index, colour in enumerate(row):
                bit = (index * 2) % 32
                colour = 0 if colour == ' ' else int(colour)
                if bit == 0 and index != 0:
                    rowdata.append(word)
                    word = 0
                word |= (colour<<bit)
            rowdata.append(word)
            data.append(rowdata)
        return data


class Characters(object):

    def __init__(self, json_file):
        with open(json_file, 'r') as fh:
            data = json.loads(fh.read())
        self.width = data['width']
        self.height = data['height']

        self.characters = {}
        for char, rows in data['characters'].items():
            bm = Bitmap(self.width, self.height)
            bm.grid = [str(row) for row in rows]
            self.characters[char] = bm

    def bitmap(self, string, bg=None, fg=None):
        bm = Bitmap(0, 0)
        bg = ' ' if bg is None else str(bg)[:1]
        fg = '1' if fg is None else str(fg)[:1]
        for char in string:
            if char in self.characters:
                char_bm = self.characters[char]
                if bg != ' ' or fg != '1':
                    char_bm.copy()
                char_bm.replace(' ', bg)
                char_bm.replace('1', fg)
                bm.append(char_bm)
            else:
                raise Exception("Not showing: %r" % (char,))

        return bm


class ProgressBar(object):

    def __init__(self, width, height, border=3, fill=0, bar=1):
        self.width = width
        self.height = height
        if border is not None:
            self.border = str(border) if border else ' '
        else:
            self.border = None
        self.fill = str(fill) if fill else ' '
        self.bar = str(bar) if bar else ' '
        self.bm = Bitmap(width, height, bg=self.fill)
        self.bm.set_bg(0)

        # Put the border around it
        if self.border is not None:
            # only if we've got one configured
            self.bm.hline(self.border, x=0, y=0, width=self.width)
            self.bm.hline(self.border, x=0, y=self.height - 1, width=self.width)
            self.bm.vline(self.border, x=0, y=0, height=self.height)
            self.bm.vline(self.border, x=self.width - 1, y=0, height=self.height)

    def bitmap(self, percentage):
        if self.border is None:
            x0 = 0
            y0 = 0
            width = self.width
            height = self.height
        else:
            x0 = 1
            y0 = 1
            width = self.width - 2
            height = self.height - 2

        bm = self.bm.copy()
        bar_width = int((width + 1) * percentage / 100)
        if bar_width:
            for y in range(height):
                bm.hline(self.bar, x=x0, y=y0 + y, width=bar_width)
        return bm


class ProgressBarDigits(ProgressBar):

    def __init__(self, *args, **kwargs):
        separator = kwargs.pop('separator', 2)
        super(ProgressBarDigits, self).__init__(*args, **kwargs)
        self.separator = separator

    def bitmap(self, percentage):
        bm = super(ProgressBarDigits, self).bitmap(percentage)

        bm.append_columns(2)
        percent = chars.bitmap('{}%'.format(percentage), fg=3)


if __name__ == '__main__':
    import pprint

    digits_file = 'digits.json'
    if not os.path.isfile(digits_file):
        digits_file = os.path.join(os.path.dirname(__file__), digits_file)
    chars = Characters(digits_file)


    percent = chars.bitmap('25%')
    pprint.pprint(percent.grid)

    bar = ProgressBar(20, 6)
    import pprint
    pprint.pprint(bar.bitmap(0).grid)
    pprint.pprint(bar.bitmap(7).grid)
    pprint.pprint(bar.bitmap(25).grid)
    pprint.pprint(bar.bitmap(99).grid)

    for pct in range(0, 100, 6):
        bm = bar.bitmap(pct)
        bm.append_columns(2)
        percent = chars.bitmap('{}%'.format(pct), fg=3)
        bm.append(percent, align=0)
        #bm.border(2)
        bm.set_width(width=50, align=0)
        print("\n")
        pprint.pprint(bm.grid)
