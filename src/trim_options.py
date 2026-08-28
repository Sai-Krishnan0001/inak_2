#!/usr/bin/env python3
"""Trim over-long distractors by deleting a trailing subordinate clause.

Why this exists: options written at 140-160 characters are unwieldy to read and
they create the long/short spread that gate 3c measures. The tail is almost
always a justifying clause the option does not need -- the reasoning belongs in
`why` and `traps`, not in the option text.

This is a PURE DELETION. It never invents text. A cut is only accepted when the
remainder is still a substantive, cleanly-terminated option, and every change is
printed so it can be re-read (the scrub_absolutes lesson: re-read what it
changed before trusting it).

    python3 src/trim_options.py --report   # show what would change
    python3 src/trim_options.py            # apply
"""
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
AUTHORED = SRC / "authored"
FIELDS = ("concept", "tier", "stem", "correct", "d1", "d2", "d3", "why", "traps")

TARGET = 78    # only consider options longer than this
FLOOR = 55     # never cut below this -- a stub is worse than a long option

# Trailing clauses that carry justification rather than the option's substance.
# Ordered longest-first so the most specific marker wins.
TAILS = [
    r",\s+so that\b", r"\s+so that\b",
    r",\s+which\b", r",\s+since\b", r",\s+because\b",
    r",\s+and\b", r",\s+rather than\b", r"\s+rather than\b",
    r",\s+regardless of\b", r"\s+regardless of\b",
    r",\s+even (?:if|though)\b", r"\s+even (?:if|though)\b",
    r",\s+while\b", r"\s+while\b",
    r",\s+without\b", r"\s+without\b",
    r",\s+before\b", r",\s+once\b", r"\s+once\b",
    r",\s+whenever\b", r"\s+whenever\b",
    r",\s+depending on\b", r"\s+depending on\b",
]
DANGLING = re.compile(r"\b(the|a|an|of|to|and|or|in|on|for|with|that|its|their|this|these)$", re.I)


def trim(text):
    """Return the shortest acceptable trim of `text`, or None if no clean cut."""
    best = None
    for pat in TAILS:
        for m in re.finditer(pat, text):
            head = text[:m.start()].rstrip(" ,;:")
            if len(head) < FLOOR:
                continue
            if DANGLING.search(head):
                continue
            if head.endswith(("-", "(")):
                continue
            # prefer the longest cut that still clears the floor
            if best is None or len(head) < len(best):
                best = head
    return best


def main():
    report = "--report" in sys.argv
    # --correct also trims the correct answer (field 3). Authoring drifts toward
    # writing the correct option fuller than the distractors, which is the exact
    # tell gate 3 measures; trimming its justification tail (which lives in `why`
    # anyway) pulls it back into the distractor band.
    fields = (3, 4, 5, 6) if "--correct" in sys.argv else (4, 5, 6)
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--file="):
            only = a.split("=", 1)[1]
    global TARGET
    global FLOOR
    for a in sys.argv[1:]:
        if a.startswith("--target="):
            TARGET = int(a.split("=", 1)[1])
        if a.startswith("--floor="):
            FLOOR = int(a.split("=", 1)[1])
    changed = 0
    considered = 0
    for path in sorted(AUTHORED.glob("d?-??.psv")):
        if only and not path.name.startswith(only):
            continue
        lines = path.read_text().splitlines()
        out = []
        for raw in lines:
            if not raw.strip() or raw.strip().startswith("#"):
                out.append(raw)
                continue
            parts = raw.split("|")
            if len(parts) != 9:
                out.append(raw)
                continue
            for idx in fields:
                if len(parts[idx]) <= TARGET:
                    continue
                considered += 1
                head = trim(parts[idx])
                if head and len(head) < len(parts[idx]):
                    print(f"{path.name} field{idx}  {len(parts[idx])} -> {len(head)}")
                    print(f"   was: {parts[idx]}")
                    print(f"   now: {head}")
                    parts[idx] = head
                    changed += 1
            out.append("|".join(parts))
        if not report:
            path.write_text("\n".join(out) + "\n")
    print(f"\n{changed} of {considered} over-long distractors trimmed"
          f"{' (report only, nothing written)' if report else ''}")


if __name__ == "__main__":
    main()
