#!/usr/bin/env python3
"""Validate a Quizlet custom-import .txt file.

Usage:
    python validate_quizlet.py output.txt [more.txt ...]

Exit code 0 = every file passed. Exit code 1 = at least one file failed.

The checks below are numbered to match the checklist in SKILL.md section 6, in
the same order, so an agent that cannot execute code can walk the prose version
and get the identical result.

Format under test (see SKILL.md section 1):

    FRONT $$$ BACK ### FRONT $$$ BACK ### ...

with zero characters of any kind adjacent to the separators.
"""

import codecs
import glob
import re
import sys

CARD_SEP = "###"
TERM_SEP = "$$$"

# "A. text" - capital letter, period, exactly one space, then non-space content.
OPTION_RE = re.compile(r"^([A-Z])\. (\S.*)$")

# Leftover question numbering at the start of a front: "Q7.", "Cau 12:", "3)",
# "15.", "Question 4 -". A bare number that is part of the prose ("1945 la nam
# nao", "Dieu 15 quy dinh") does not match, because a delimiter must follow the
# digits and be followed by whitespace.
NUMBERING_RE = re.compile(
    r"^\s*(?:c[âa]u|question|quest|q|b[àa]i|item|no)?\s*\d+\s*[.):\]\-]\s+",
    re.IGNORECASE,
)

# An option prefix that was never normalized to "A. ": "a)", "b.", "1.", "2)".
# These are unambiguous option markers, so finding one below a stem's first line
# means step 3 of the workflow was skipped.
UNNORMALIZED_OPTION_RE = re.compile(r"^(?:[a-z][).:]|\d{1,2}[).:])\s+\S")

# A bullet is a weaker signal - it can legitimately open a continuation line of a
# multi-line stem - so it is reported as a warning rather than an error.
BULLET_OPTION_RE = re.compile(r"^[-•*+]\s+\S")


SELECTION_NOTE_RE = re.compile(
    r"\(\s*(?:(?:chọn|lựa chọn|câu hỏi lựa chọn)\b|\d+\s*đáp án\b)[^()]*\)",
    re.IGNORECASE,
)
SELECTION_LINE_RE = re.compile(
    r"^\s*\(\s*(?:(?:chọn|lựa chọn|câu hỏi lựa chọn)\b|\d+\s*đáp án\b)[^()]*\)\s*$",
    re.IGNORECASE,
)


class Report:
    def __init__(self, path):
        self.path = path
        self.errors = []
        self.warnings = []
        self.cards = 0

    def error(self, check, message, card=None):
        where = "" if card is None else " (card %d)" % card
        self.errors.append("check %-2d%s: %s" % (check, where, message))

    def warn(self, check, message, card=None):
        where = "" if card is None else " (card %d)" % card
        self.warnings.append("check %-2d%s: %s" % (check, where, message))

    @property
    def ok(self):
        return not self.errors


def snippet(text, limit=60):
    one_line = text.replace("\n", "\\n")
    if len(one_line) > limit:
        one_line = one_line[:limit] + "..."
    return repr(one_line)


def check_bytes(raw, rep):
    """Check 1 and part of check 6: encoding, BOM, CR, leading whitespace."""
    if raw.startswith(codecs.BOM_UTF8):
        rep.error(1, "file starts with a UTF-8 BOM; write UTF-8 without BOM")
    if b"\r" in raw:
        rep.error(1, "file contains a carriage return; write LF line endings only")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        rep.error(1, "file is not valid UTF-8: %s" % exc)
        return None


def check_separators(text, rep):
    """Checks 2 and 6: nothing may touch ### , and the file edges are clean."""
    for bad, label in (
        ("\n" + CARD_SEP, "a newline immediately before ###"),
        (CARD_SEP + "\n", "a newline immediately after ###"),
        (" " + CARD_SEP, "a space immediately before ###"),
        (CARD_SEP + " ", "a space immediately after ###"),
        ("\t" + CARD_SEP, "a tab immediately before ###"),
        (CARD_SEP + "\t", "a tab immediately after ###"),
    ):
        if bad in text:
            rep.error(
                2,
                "%s (occurs %d time(s)); cards must be joined by ### with nothing "
                "between them" % (label, text.count(bad)),
            )

    if "\n\n" in text:
        rep.error(5, "file contains a blank line")

    if text[:1].isspace():
        rep.error(6, "file begins with whitespace")
    if text.endswith("\n"):
        rep.error(6, "file ends with a newline; it must end at the last answer character")
    if text.endswith(CARD_SEP):
        rep.error(6, "file ends with a trailing ###")


def split_front(front):
    """Return (stem_lines, option_lines).

    Options are the trailing run of lines that look like "A. text". A stem always
    keeps at least its first line.
    """
    lines = front.split("\n")
    i = len(lines)
    while i > 1 and OPTION_RE.match(lines[i - 1]):
        i -= 1
    return lines[:i], lines[i:]


def check_card(index, card, rep, seen_fronts):
    if card == "":
        rep.error(3, "empty card", index)
        return

    if card.count(TERM_SEP) != 1:
        rep.error(
            4,
            "card contains %d occurrences of $$$ (expected exactly 1): %s"
            % (card.count(TERM_SEP), snippet(card)),
            index,
        )
        return

    front, back = card.split(TERM_SEP)

    # Check 5 - no stray whitespace on either side or at a line end.
    if front != front.strip():
        rep.error(5, "front has leading or trailing whitespace: %s" % snippet(front), index)
    if back != back.strip():
        rep.error(5, "back has leading or trailing whitespace: %s" % snippet(back), index)
    for line in card.split("\n"):
        if line != line.rstrip():
            rep.error(5, "line has trailing whitespace: %s" % snippet(line), index)

    if not front.strip():
        rep.error(3, "card has an empty front", index)
        return
    if not back.strip():
        rep.error(3, "card has an empty back", index)
        return

    stem_lines, option_lines = split_front(front)

    # Check 12 - selection instructions belong on their own term-side line,
    # immediately after the stem, never in the definition.
    if SELECTION_NOTE_RE.search(back):
        rep.error(
            12,
            "selection instruction belongs in the front on its own line, not in "
            "the back: %s" % snippet(back),
            index,
        )
    front_selection_lines = [
        n for n, line in enumerate(stem_lines) if SELECTION_LINE_RE.match(line)
    ]
    if SELECTION_NOTE_RE.search(stem_lines[0]) or (
        front_selection_lines and front_selection_lines != [1]
    ):
        rep.error(
            12,
            "selection instruction must be its own line immediately after the "
            "question stem",
            index,
        )

    # Check 7 - leftover question numbering.
    if NUMBERING_RE.match(stem_lines[0]):
        rep.error(
            7,
            "front still starts with question numbering: %s" % snippet(stem_lines[0]),
            index,
        )

    # Check 8 - option lines are well formed, contiguous, and consecutive from A.
    for line in stem_lines[1:]:
        if OPTION_RE.match(line):
            rep.error(
                8,
                "an option line appears above the stem's last line, so the options "
                "are not contiguous at the end of the front: %s" % snippet(line),
                index,
            )
        elif UNNORMALIZED_OPTION_RE.match(line):
            rep.error(
                8,
                "option prefix was never normalized to 'A. ': %s" % snippet(line),
                index,
            )
        elif BULLET_OPTION_RE.match(line):
            rep.warn(
                8,
                "line looks like a bulleted option that was never normalized to "
                "'A. ' (ignore if it is part of a multi-line stem): %s" % snippet(line),
                index,
            )

    options = {}
    if option_lines:
        if len(option_lines) < 2:
            rep.error(
                8,
                "only one option line found; a question with options needs at "
                "least two: %s" % snippet(option_lines[0]),
                index,
            )
        expected = [chr(ord("A") + n) for n in range(len(option_lines))]
        actual = [OPTION_RE.match(line).group(1) for line in option_lines]
        if actual != expected:
            rep.error(
                8,
                "option letters are %s but must run consecutively from A: %s"
                % ("".join(actual), "".join(expected)),
                index,
            )
        for line in option_lines:
            m = OPTION_RE.match(line)
            options[m.group(1)] = m.group(2)

    back_lines = back.split("\n")

    if options:
        # Check 9 - every back line is "<letter>. <exact option text>", with an
        # optional " (annotation)" appended.
        letters = []
        for line in back_lines:
            m = OPTION_RE.match(line)
            if not m:
                rep.error(
                    9,
                    "back line is not '<letter>. <option text>': %s" % snippet(line),
                    index,
                )
                continue
            letter, rest = m.group(1), m.group(2)
            letters.append(letter)
            if letter not in options:
                rep.error(
                    9,
                    "back names option %s but the front has no option %s"
                    % (letter, letter),
                    index,
                )
                continue
            text = options[letter]
            if rest == text:
                continue
            if rest.startswith(text + " (") and rest.endswith(")"):
                continue
            rep.error(
                9,
                "back text for option %s does not match the front. front=%s "
                "back=%s" % (letter, snippet(text), snippet(rest)),
                index,
            )
        if len(set(letters)) != len(letters):
            rep.error(9, "back repeats the same option letter", index)
        if letters != sorted(letters):
            # A warning, not an error: an ordering question's back is deliberately
            # in answer order rather than letter order (references/edge-cases.md).
            rep.warn(
                9,
                "multi-answer back is not in letter order (correct only if this is "
                "an ordering question)",
                index,
            )
    else:
        # Check 10 - a question with no options must not gain a letter prefix.
        if re.match(r"^[A-Z]\.\s", back_lines[0]):
            rep.error(
                10,
                "front has no options but the back starts with a letter prefix: %s"
                % snippet(back_lines[0]),
                index,
            )

    # Check 11 - duplicate fronts are usually a parsing error.
    if front in seen_fronts:
        rep.warn(
            11,
            "duplicate front, also card %d: %s" % (seen_fronts[front], snippet(front)),
            index,
        )
    else:
        seen_fronts[front] = index


def validate(path):
    rep = Report(path)
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        rep.error(0, "cannot read file: %s" % exc)
        return rep

    text = check_bytes(raw, rep)
    if text is None:
        return rep
    text = text.lstrip("﻿")

    if not text:
        rep.error(3, "file is empty")
        return rep

    check_separators(text, rep)

    cards = text.split(CARD_SEP)
    rep.cards = len(cards)
    seen_fronts = {}
    for i, card in enumerate(cards, start=1):
        check_card(i, card, rep, seen_fronts)

    return rep


def main(argv):
    # Findings quote the source text, which is routinely Vietnamese, Japanese or
    # Greek. A Windows console defaults to a legacy codepage and would raise
    # UnicodeEncodeError mid-report, turning a useful failure list into a
    # traceback. Never let the console encoding decide whether validation works.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    paths = []
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        matches = glob.glob(arg)
        paths.extend(matches or [arg])
    quiet = "--quiet" in argv[1:] or "-q" in argv[1:]
    if not paths:
        print(__doc__.strip())
        return 2

    failed = False
    for path in paths:
        rep = validate(path)
        if rep.ok:
            if not quiet:
                print("PASS  %s  (%d cards)" % (path, rep.cards))
            for w in rep.warnings:
                print("  warning  %s" % w)
        else:
            failed = True
            print("FAIL  %s  (%d cards parsed)" % (path, rep.cards))
            for e in rep.errors:
                print("  error    %s" % e)
            for w in rep.warnings:
                print("  warning  %s" % w)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
