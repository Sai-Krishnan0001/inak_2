#!/usr/bin/env python3
"""Length-parity tooling for the authored bank.

The leak this exists to close: correct answers get written fuller than
distractors, so "always pick the longest option" beats chance. Templating the
lengths does not fix it -- it just moves the bulge to another rank (measured:
trimming every justification tail took 87.6% longest to 46.8% longest / 44.0%
shortest). What works is four options of genuinely similar length.

    python3 src/parity.py worklist d1-01     # what to rewrite, with a target length
    python3 src/parity.py apply fixes.tsv    # apply "source<TAB>new correct text"
"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
AUTHORED = SRC / "authored"
FIELDS = ("concept", "tier", "stem", "correct", "d1", "d2", "d3", "why", "traps")


def target_for(index, dlens):
    """Cycle the correct answer's intended length rank so no rank dominates.

    rank 0 = longer than every distractor, rank 3 = shorter than every one.
    Returned as a character count to aim at while rewriting.
    """
    lo, mid, hi = sorted(dlens)
    slot = index % 4
    if slot == 0:
        return hi + 6, "longest"
    if slot == 1:
        return (mid + hi) // 2, "2nd-longest"
    if slot == 2:
        return (lo + mid) // 2, "3rd-longest"
    return max(38, lo - 6), "shortest"


def worklist(stem_filter):
    idx = 0
    for path in sorted(AUTHORED.glob("d?-??.psv")):
        if stem_filter and not path.stem.startswith(stem_filter):
            continue
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) != 9:
                continue
            item = dict(zip(FIELDS, parts))
            dlens = [len(item["d1"]), len(item["d2"]), len(item["d3"])]
            tgt, label = target_for(idx, dlens)
            idx += 1
            cur = len(item["correct"])
            if abs(cur - tgt) <= 5:
                continue
            print(f"{path.name}:{lineno}\ttarget={tgt}\t({label})\tnow={cur}\td={dlens}")
            print(f"    {item['correct']}")


def apply(tsv_path):
    """Apply "source<TAB>text" (rewrites the correct answer) or
    "source<TAB>field<TAB>text" where field is 3 (correct) or 4/5/6 (distractors).

    Lengthening a distractor above the correct answer is usually the better move:
    it pulls an item out of rank 0 without pushing anything into rank 3, and a
    fuller distractor is a better distractor anyway.
    """
    fixes = {}
    for line in Path(tsv_path).read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        bits = line.split("\t")
        if len(bits) >= 3 and bits[1].strip().isdigit():
            source, field, text = bits[0], int(bits[1]), "\t".join(bits[2:])
        else:
            source, field, text = bits[0], 3, "\t".join(bits[1:])
        if field not in (3, 4, 5, 6):
            sys.exit(f"FATAL: field {field} for {source} is not 3-6")
        fixes.setdefault(source.strip(), []).append((field, text.strip()))

    changed = 0
    for path in sorted(AUTHORED.glob("d?-??.psv")):
        lines = path.read_text().splitlines()
        out = []
        for lineno, raw in enumerate(lines, 1):
            key = f"{path.name}:{lineno}"
            if key in fixes and not raw.strip().startswith("#"):
                parts = raw.split("|")
                if len(parts) == 9:
                    for field, text in fixes[key]:
                        if "|" in text:
                            sys.exit(f"FATAL: replacement for {key} contains a pipe")
                        parts[field] = text
                        changed += 1
                    raw = "|".join(parts)
            out.append(raw)
        path.write_text("\n".join(out) + "\n")
    print(f"applied {changed} of {sum(len(v) for v in fixes.values())} fixes")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "worklist":
        worklist(sys.argv[2] if len(sys.argv) > 2 else "")
    elif sys.argv[1] == "apply":
        apply(sys.argv[2])
    else:
        sys.exit(__doc__)
