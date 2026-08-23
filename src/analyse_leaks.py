#!/usr/bin/env python3
"""Report the two answer-leaking tells, per file and per item.

    python3 src/analyse_leaks.py            # summary + worst offenders
    python3 src/analyse_leaks.py --fix-list # emit source refs needing a length fix
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent
AUTHORED = SRC / "authored"
FIELDS = ("concept", "tier", "stem", "correct", "d1", "d2", "d3", "why", "traps")


def rows():
    for path in sorted(AUTHORED.glob("d?-??.psv")):
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) != len(FIELDS):
                continue
            item = dict(zip(FIELDS, (p.strip() for p in parts)))
            item["source"] = f"{path.name}:{lineno}"
            item["file"] = path.name
            yield item


def main():
    fix_list = "--fix-list" in sys.argv
    per_file = defaultdict(Counter)
    ranks = Counter()
    offenders = []
    total = 0

    for r in rows():
        total += 1
        c = len(r["correct"])
        ds = [len(r["d1"]), len(r["d2"]), len(r["d3"])]
        # rank of the correct answer by length, 0 = longest
        rank = sum(1 for d in ds if d > c)
        ranks[rank] += 1
        per_file[r["file"]][rank] += 1
        longest_d = max(ds)
        if rank == 0:
            offenders.append((c - longest_d, r["source"], c, ds))

    print(f"{total} items")
    print("correct-answer length rank (0 = longest option):")
    for k in range(4):
        label = ["longest", "2nd", "3rd", "shortest"][k]
        print(f"  {label:9} {ranks[k]:5}  {100*ranks[k]/max(total,1):5.1f}%")

    offenders.sort(reverse=True)
    if fix_list:
        for delta, source, c, ds in offenders:
            print(f"{source}\t+{delta}\tcorrect={c}\tdistractors={ds}")
        return

    print("\nper file (share where correct is longest):")
    for name in sorted(per_file):
        n = sum(per_file[name].values())
        print(f"  {name}  {100*per_file[name][0]/n:5.1f}%  ({per_file[name][0]}/{n})")

    print("\n20 biggest gaps (correct minus longest distractor):")
    for delta, source, c, ds in offenders[:20]:
        print(f"  {source:16} +{delta:3}  correct={c:3}  distractors={ds}")


if __name__ == "__main__":
    main()
