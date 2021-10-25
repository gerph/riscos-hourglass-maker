#!/usr/bin/env python
"""
Simple parser to extract the font details from a specific BDF font.
"""

import re

import templates

output_file = '../digits.json'
template_file = 'digits.json.j2'

configs = {
        'spleen': {
                'input_file': 'spleen/spleen-6x12.bdf',
                'trim_top': 1,
                'trim_bottom': 3,
                'trim_left': 0,
                'trim_right': 0,
            },

        'bitocra': {
                'input_file': 'bitocra/bitocra7.bdf',
                'trim_top': 1,
                'trim_bottom': 1,
                'trim_left': 0,
                'trim_right': 0,
            },

        'leovilok': {
                'input_file': 'leovilok/3x6.bdf',
                'trim_top': 0,
                'trim_bottom': 2,
                'trim_left': 0,
                'trim_right': 0,
            },

        'leovilok-sqapps': {
                'input_file': 'leovilok/sqaps.bdf',
                'trim_top': 2,
                'trim_bottom': 1,
                'trim_left': 0,
                'trim_right': 1,
            },
    }

# Configuration to use
digits_config = 'spleen'

config = configs[digits_config]

input_file = config['input_file']
trim_top = config['trim_top']
trim_bottom = config['trim_bottom']
trim_left = config['trim_left']
trim_right = config['trim_right']


# Format by examination only; nothing very complex here.
characters_wanted = (' ', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '%')

width = None
height = None
characters = {}

font_bbox_re = re.compile(r'FONTBOUNDINGBOX (\d+) (\d+)')
start_re = re.compile(r'ENCODING (.*)$')
end_re = re.compile(r'ENDCHAR')

in_character = 0

with open(input_file, 'r') as fh:
    for line in fh:
        line = line.strip()

        match = font_bbox_re.match(line)
        if match:
            source_width = int(match.group(1))
            width = source_width - trim_left - trim_right
            source_height = int(match.group(2))
            height = source_height - trim_top - trim_bottom

        match = start_re.match(line)
        if match:
            char = match.group(1)
            char = int(char)
            if char < 256:
                char = chr(char)
                if char in characters_wanted:
                    print("Found %s" % (char,))
                    in_character = char
                    characters[in_character] = []

        match = end_re.match(line)
        if match:
            if in_character:
                # Ensure that the characters are padded out to the width and height
                rows = characters[in_character]
                for y in range(source_height):
                    if len(rows) <= y:
                        rows.append(' ' * width)
                    if len(rows[y]) < width:
                        rows[y] += ' ' * (width - len(rows[y]))
                # Apply trimming
                if trim_bottom:
                    characters[in_character] = characters[in_character][:-trim_bottom]
                characters[in_character] = characters[in_character][trim_top:]
                in_character = None

        if in_character:
            # Decode from hex.
            try:
                value = int(line, 16)
                s = bin(value)[2:].replace('0', ' ')
                if len(s) < 8:
                    s = (' ' * (8 - len(s))) + s
                # Truncate down to the width supplied
                s = s[:source_width]
                if trim_right:
                    s = s[:-trim_right]
                s = s[trim_left:]
                characters[in_character].append(s)
            except ValueError:
                # Just ignore things we don't understand
                pass

template = templates.Template('.')

template.render_to_file(template_file,
                        output_file,
                        template_vars={
                            'characters': characters,
                            'width': width,
                            'height': height
                        })
