"""Minimal Arabic shaping and right-to-left ordering for PDF text.

PDF text is drawn glyph by glyph, left to right, so Arabic must be prepared first:
each letter is replaced by its contextual form (isolated, final, initial, medial)
from the Unicode "Arabic Presentation Forms-B" block, lam-alef becomes one
ligature, and each line is put in visual (right-to-left) order while Latin words
and numbers inside it keep their own left-to-right order. This covers the modern
Arabic letters used in work orders and explanations; vowel marks are dropped.
No third-party package is needed. DejaVu Sans contains these glyphs.
"""

import re

# letter: (isolated, final, initial, medial); letters with two forms join on the right only.
FORMS = {
    "ء": ("ﺀ",), "آ": ("ﺁ", "ﺂ"), "أ": ("ﺃ", "ﺄ"),
    "ؤ": ("ﺅ", "ﺆ"), "إ": ("ﺇ", "ﺈ"),
    "ئ": ("ﺉ", "ﺊ", "ﺋ", "ﺌ"), "ا": ("ﺍ", "ﺎ"),
    "ب": ("ﺏ", "ﺐ", "ﺑ", "ﺒ"), "ة": ("ﺓ", "ﺔ"),
    "ت": ("ﺕ", "ﺖ", "ﺗ", "ﺘ"), "ث": ("ﺙ", "ﺚ", "ﺛ", "ﺜ"),
    "ج": ("ﺝ", "ﺞ", "ﺟ", "ﺠ"), "ح": ("ﺡ", "ﺢ", "ﺣ", "ﺤ"),
    "خ": ("ﺥ", "ﺦ", "ﺧ", "ﺨ"), "د": ("ﺩ", "ﺪ"),
    "ذ": ("ﺫ", "ﺬ"), "ر": ("ﺭ", "ﺮ"), "ز": ("ﺯ", "ﺰ"),
    "س": ("ﺱ", "ﺲ", "ﺳ", "ﺴ"), "ش": ("ﺵ", "ﺶ", "ﺷ", "ﺸ"),
    "ص": ("ﺹ", "ﺺ", "ﺻ", "ﺼ"), "ض": ("ﺽ", "ﺾ", "ﺿ", "ﻀ"),
    "ط": ("ﻁ", "ﻂ", "ﻃ", "ﻄ"), "ظ": ("ﻅ", "ﻆ", "ﻇ", "ﻈ"),
    "ع": ("ﻉ", "ﻊ", "ﻋ", "ﻌ"), "غ": ("ﻍ", "ﻎ", "ﻏ", "ﻐ"),
    "ف": ("ﻑ", "ﻒ", "ﻓ", "ﻔ"), "ق": ("ﻕ", "ﻖ", "ﻗ", "ﻘ"),
    "ك": ("ﻙ", "ﻚ", "ﻛ", "ﻜ"), "ل": ("ﻝ", "ﻞ", "ﻟ", "ﻠ"),
    "م": ("ﻡ", "ﻢ", "ﻣ", "ﻤ"), "ن": ("ﻥ", "ﻦ", "ﻧ", "ﻨ"),
    "ه": ("ﻩ", "ﻪ", "ﻫ", "ﻬ"), "و": ("ﻭ", "ﻮ"),
    "ى": ("ﻯ", "ﻰ"), "ي": ("ﻱ", "ﻲ", "ﻳ", "ﻴ"),
}
LAM_ALEF = {"آ": ("ﻵ", "ﻶ"), "أ": ("ﻷ", "ﻸ"),
            "إ": ("ﻹ", "ﻺ"), "ا": ("ﻻ", "ﻼ")}
TATWEEL = "ـ"
MARKS = re.compile("[ً-ٰٟۖ-ۭ]")  # vowel marks: dropped
ARABIC = re.compile("[؀-ۿﭐ-﷿ﹰ-﻿]")
MIRROR = str.maketrans("()[]{}<>«»", ")(][}{><»«")
# Left-to-right runs inside an Arabic line: Latin words, numbers, units, dates and the symbols between them.
LTR_RUN = re.compile(r"[A-Za-z0-9Δ][A-Za-z0-9Δ*.,:/%+\-=±°²³·_ ]*[A-Za-z0-9%*²³]|[A-Za-z0-9]")


def has_arabic(text):
    return bool(ARABIC.search(text or ""))


def _joins_left(ch):
    return ch == TATWEEL or len(FORMS.get(ch, ())) == 4


def _joins(ch):
    return ch == TATWEEL or ch in FORMS


def shape(text):
    """Replace Arabic letters with their contextual presentation forms (logical order kept)."""
    chars = list(MARKS.sub("", text))
    out, i = [], 0
    while i < len(chars):
        ch = chars[i]
        if ch not in FORMS:
            out.append(ch)
            i += 1
            continue
        prev = chars[i - 1] if i > 0 else ""
        joined_before = _joins_left(prev)
        if ch == "ل" and i + 1 < len(chars) and chars[i + 1] in LAM_ALEF:
            out.append(LAM_ALEF[chars[i + 1]][1 if joined_before else 0])
            i += 2
            continue
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        forms = FORMS[ch]
        joined_after = len(forms) == 4 and _joins(nxt)
        if joined_before and joined_after:
            out.append(forms[3])
        elif joined_before and len(forms) > 1:
            out.append(forms[1])
        elif joined_after:
            out.append(forms[2])
        else:
            out.append(forms[0])
        i += 1
    return "".join(out)


def visual(line):
    """One line in visual order: right-to-left overall, Latin/number runs left-to-right inside it."""
    shaped = shape(line)
    if not has_arabic(shaped):
        return shaped
    parts, last = [], 0
    for match in LTR_RUN.finditer(shaped):
        if match.start() > last:
            parts.append(shaped[last:match.start()][::-1].translate(MIRROR))
        parts.append(match.group(0))
        last = match.end()
    if last < len(shaped):
        parts.append(shaped[last:][::-1].translate(MIRROR))
    return "".join(reversed(parts))


def wrap(line, width, measure):
    """Wrap a logical-order line to ``width`` (``measure(text)`` gives its width) before visual ordering,
    so the first visual line holds the start of the sentence."""
    words, rows, current = line.split(" "), [], ""
    for word in words:
        trial = f"{current} {word}" if current else word
        if current and measure(shape(trial)) > width:
            rows.append(current)
            current = word
        else:
            current = trial
    rows.append(current)
    return rows
