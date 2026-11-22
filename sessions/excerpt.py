"""Print lines of a screen capture with Kindle-safe characters.

    python3 sessions/excerpt.py <capture> <first> <last>

The book's code font has no glyphs for the terminal's symbols, so an
excerpt maps them to plain characters. The book states the mapping in
chapter 1. Blank runs of more than one line collapse to one.
"""

import sys

MAP = {
    "❯": ">", "●": "*", "⎿": "|", "⏵": ">", "⏸": "||", "✻": "*",
    "✢": "*", "✔": "v", "☐": "[ ]", "☒": "[x]", "⚠": "!", "⌕": "",
    "←": "<-", "→": "->", "↑": "^", "↓": "v", "≥": ">=", "−": "-",
    "─": "-", "╌": "-", "│": "|", "┌": "+", "┐": "+", "└": "+",
    "┘": "+", "├": "+", "┤": "+", "┬": "+", "┴": "+", "┼": "+",
    "╭": "+", "╮": "+", "╯": "+", "╰": "+", "▎": "|",
    "›": ">",
}


def clean(line: str) -> str:
    return "".join(MAP.get(c, c) for c in line).rstrip()


def main() -> None:
    path, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    lines = open(path, encoding="utf-8").read().splitlines()
    blank = False
    for line in lines[first - 1 : last]:
        out = clean(line)
        if not out.strip():
            if blank:
                continue
            blank = True
        else:
            blank = False
        print(out)


if __name__ == "__main__":
    main()
