#!/usr/bin/env python3
"""Parse the authored PSV files, place the answer key, run the gates, emit bank.json.

Usage:
    python3 src/build_bank.py            # gate, then write src/bank.json
    python3 src/build_bank.py --report   # gate only, write nothing
    python3 src/build_bank.py --loose    # warn instead of fail (authoring only)
"""

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

SRC = Path(__file__).resolve().parent
AUTHORED = SRC / "authored"

# CCAO-F blueprint, verbatim from the official exam guide (v1.0, July 2026,
# section 6) — see shared/ccao/SYLLABUS.md. Domain NAMES are the guide's, because
# they are what appears on the candidate's score report.
#
# `weight` is the real exam weighting and drives how a drawn session is
# apportioned. `count` is the single-answer items held, `multi` the
# multiple-response ones. `count` must divide by 4 for the answer-key balance
# (gate 2) — 21% of 2000 would be 420, which does not, so d2 holds 416.
DOMAINS = [
    {"id": "d1", "name": "Prompting and Task Execution",          "short": "Prompting",       "weight": 14, "count": 296, "multi": 20, "accent": "cyan"},
    {"id": "d2", "name": "Output Evaluation and Validation",      "short": "Output Eval",     "weight": 21, "count": 444, "multi": 29, "accent": "azure"},
    {"id": "d3", "name": "Product and Model Selection",           "short": "Model Choice",    "weight": 12, "count": 252, "multi": 18, "accent": "indigo"},
    {"id": "d4", "name": "Workflow Integration and Solution Design","short": "Workflow",      "weight": 16, "count": 336, "multi": 24, "accent": "purple"},
    {"id": "d5", "name": "Configuration and Knowledge Management","short": "Configuration",   "weight": 12, "count": 252, "multi": 18, "accent": "teal"},
    {"id": "d6", "name": "Governance, Risk, and Responsible Use", "short": "Governance",      "weight": 15, "count": 316, "multi": 21, "accent": "peri"},
    {"id": "d7", "name": "Troubleshooting and Optimization",      "short": "Troubleshooting", "weight": 10, "count": 208, "multi": 16, "accent": "mint"},
]

COUNT = {d["id"]: d["count"] for d in DOMAINS}
TOTAL = sum(d["count"] + d["multi"] for d in DOMAINS)

# Two item shapes, because the real exam has two. The official exam guide
# (v1.0, July 2026, section 5) specifies "Multiple-choice and multiple-response
# items; each item states how many responses to select".
#   single (dN-XX.psv, 9 fields)  — 4 options, exactly 1 correct, written first
#   multi  (dN-mX.psv, 11 fields) — 5 options, `ncorrect` (2 or 3) correct, written first
FIELDS = ("concept", "objective", "tier", "stem", "correct", "d1", "d2", "d3", "why", "traps")
FIELDS_MULTI = ("concept", "objective", "tier", "ncorrect", "stem",
                "o1", "o2", "o3", "o4", "o5", "why", "traps")
MULTI_OPTS = 5

# The exam guide publishes 30 second-level objectives under the seven domains and
# says items are written against them. Domain weights alone do not make a bank
# valid: it can sit exactly on the weights and still leave an objective at zero,
# which is what this bank did for 3.4 before the objective field existed.
OBJECTIVES = json.loads((SRC.parent.parent.parent / "shared" / "ccao" / "objectives.json").read_text()) \
    if (SRC.parent.parent.parent / "shared" / "ccao" / "objectives.json").exists() else None
OBJ_MIN_SHARE = 12.0   # each objective must hold at least this % of its own domain
# An interrogative stem is what makes an item an exam question rather than a
# scenario with options attached. All three of the guide's samples end with one.
INTERROGATIVE = re.compile(r"\?\s*$")

ABSOLUTES = re.compile(r"\b(always|never|all|only|every|none|any)\b", re.I)
# phrases where an absolute word is load-bearing vocabulary rather than a tell
ABSOLUTE_EXEMPT = re.compile(
    r"(read-only|must never|never retried|all seven|all four|all of the domains|"
    r"at any time|never the right|not any|any one of|every request is|none of the above)",
    re.I,
)
DEFINITIONAL = re.compile(
    r"^(what is|what are|which of the following (is|are) the definition|define |what does .{1,30} mean\?$)", re.I
)
CONCEPT_CAP = 48


def parse():
    rows, problems = [], []
    for path in sorted(AUTHORED.glob("d?-??.psv")):
        domain = path.stem.split("-")[0]
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            multi = path.stem.split("-")[1].startswith("m")
            want = FIELDS_MULTI if multi else FIELDS
            if len(parts) != len(want):
                problems.append(f"{path.name}:{lineno} has {len(parts)} fields, expected {len(want)}")
                continue
            item = dict(zip(want, parts))
            item["domain"] = domain
            item["source"] = f"{path.name}:{lineno}"
            item["kind"] = "multi" if multi else "single"
            try:
                item["tier"] = int(item["tier"])
            except ValueError:
                problems.append(f"{item['source']} tier is not a number")
                item["tier"] = 3
            if multi:
                try:
                    item["ncorrect"] = int(item["ncorrect"])
                except ValueError:
                    problems.append(f"{item['source']} ncorrect is not a number")
                    continue
                item["raw"] = [item[f"o{i}"] for i in range(1, MULTI_OPTS + 1)]
            else:
                item["ncorrect"] = 1
                item["raw"] = [item["correct"], item["d1"], item["d2"], item["d3"]]
            rows.append(item)
    return rows, problems


def _shuffle(seed_key, n):
    """Deterministic Fisher-Yates permutation of range(n), stable across runs."""
    seed = hashlib.sha256(seed_key.encode()).digest()
    perm = list(range(n))
    for i in range(n - 1, 0, -1):
        j = seed[i % len(seed)] % (i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def place_multi(rows):
    """Scatter the correct options of a multiple-response item across its five slots.

    Single-answer items get an exactly-balanced answer key (gate 2). That is not
    available here — with 2 or 3 correct of 5 there is no clean per-letter quota —
    so the guarantee is weaker but still deterministic: a hashed permutation per
    item, plus gate 2b, which checks no slot is over-represented across the bank.
    """
    for r in rows:
        if r["kind"] != "multi":
            continue
        perm = _shuffle(f"{r['source']}:multi", MULTI_OPTS)
        options = [None] * MULTI_OPTS
        answers = []
        for original, slot in enumerate(perm):
            options[slot] = r["raw"][original]
            if original < r["ncorrect"]:
                answers.append(slot)
        r["options"] = options
        r["answers"] = sorted(answers)
    return rows


def place_answers(rows):
    """Deterministically position the correct answer: even per letter, runs <= 2."""
    by_domain = defaultdict(list)
    for r in rows:
        if r["kind"] == "single":
            by_domain[r["domain"]].append(r)

    for domain, items in by_domain.items():
        prev_last = None
        for block in range((len(items) + 3) // 4):
            seed = hashlib.sha256(f"{domain}:{block}".encode()).digest()
            perm = [0, 1, 2, 3]
            # Fisher-Yates driven by the digest, so it is stable across runs
            for i in (3, 2, 1):
                j = seed[i] % (i + 1)
                perm[i], perm[j] = perm[j], perm[i]
            if perm[0] == prev_last:
                perm = perm[1:] + perm[:1]
            prev_last = perm[-1]
            for offset, slot in enumerate(perm):
                idx = block * 4 + offset
                if idx >= len(items):
                    break
                item = items[idx]
                options = [item["d1"], item["d2"], item["d3"]]
                options.insert(slot, item["correct"])
                item["options"] = options
                item["answer"] = slot
    return place_multi(rows)


def gates(rows, loose, migrating=False):
    fails, warns = [], []

    def fail(msg):
        (warns if loose else fails).append(msg)

    def fail_or_stage(msg):
        """Gates 12 and 13 define the exam-fidelity standard the bank is being
        rewritten to. They are hard gates: the default build fails until the
        rewrite is finished. `--migrating` stages them as warnings so partial
        progress can ship, and prints how far along the rewrite actually is —
        the point is that the shortfall stays visible, not that the bar moves."""
        (warns if (loose or migrating) else fails).append(msg)

    # 1 — domain counts, to the blueprint, per item shape
    singles = Counter(r["domain"] for r in rows if r["kind"] == "single")
    multis = Counter(r["domain"] for r in rows if r["kind"] == "multi")
    for d in DOMAINS:
        if singles[d["id"]] != d["count"]:
            fail(f"GATE 1 {d['id']} has {singles[d['id']]} single-answer items, expected {d['count']}")
        if multis[d["id"]] != d["multi"]:
            fail(f"GATE 1 {d['id']} has {multis[d['id']]} multiple-response items, expected {d['multi']}")
    if len(rows) != TOTAL:
        fail(f"GATE 1 total is {len(rows)}, expected {TOTAL}")

    # 2 — answer position balance (single-answer items only)
    for d in DOMAINS:
        items = [r for r in rows if r["domain"] == d["id"] and r["kind"] == "single"]
        if not items:
            continue
        letters = Counter(r["answer"] for r in items)
        for slot in range(4):
            if letters[slot] != len(items) // 4:
                fail(f"GATE 2 {d['id']} letter {'ABCD'[slot]} appears {letters[slot]}x, expected {len(items)//4}")
        run, prev = 1, None
        for r in items:
            run = run + 1 if r["answer"] == prev else 1
            prev = r["answer"]
            if run >= 3:
                fail(f"GATE 2 {d['id']} run of 3 same-position answers at {r['source']}")
                break

    # 2b — multiple-response slot balance. An exact per-letter quota is not
    # available when 2 or 3 of 5 options are correct, so this checks the weaker
    # property that matters: no slot is a disproportionately good guess.
    multi_rows = [r for r in rows if r["kind"] == "multi"]
    if multi_rows:
        slot_hits = Counter(a for r in multi_rows for a in r["answers"])
        expected = sum(len(r["answers"]) for r in multi_rows) / MULTI_OPTS
        for slot in range(MULTI_OPTS):
            drift = abs(slot_hits[slot] - expected) / max(expected, 1)
            if drift > 0.25:
                fail(f"GATE 2b multi slot {'ABCDE'[slot]} is correct {slot_hits[slot]}x "
                     f"vs {expected:.0f} expected ({drift*100:.0f}% drift, max 25%)")

    # 3 — length must not predict the answer.
    #
    # Measured as the guessing strategy itself: a test-taker who reads nothing and
    # sorts the options by length must not beat chance. Templating option lengths
    # does not fix this (it just moves the bulge to another rank) — four options of
    # genuinely similar length is what works.
    single_rows = [r for r in rows if r["kind"] == "single"]
    ranks = Counter()
    for r in single_rows:
        order = sorted(range(4), key=lambda i: -len(r["options"][i]))
        ranks[order.index(r["answer"])] += 1
    n = max(len(single_rows), 1)
    for rank in range(4):
        pct = 100 * ranks[rank] / n
        label = ["longest", "2nd-longest", "3rd-longest", "shortest"][rank]
        if pct > 34:
            fail(f"GATE 3 'always pick the {label} option' scores {pct:.1f}% (chance is 25%, max 34%)")

    # 3d — the same leak, for multiple-response. The guessing strategy here is
    # "tick the N longest options". Chance of getting a 2-of-5 item exactly right
    # by guessing is 1/10; for 3-of-5 it is also 1/10. The cap is set well above
    # that but far below what a real length tell would produce.
    if multi_rows:
        by_length = 0
        for r in multi_rows:
            k = len(r["answers"])
            longest = sorted(range(MULTI_OPTS), key=lambda i: -len(r["options"][i]))[:k]
            if sorted(longest) == r["answers"]:
                by_length += 1
        pct = 100 * by_length / len(multi_rows)
        if pct > 25:
            fail(f"GATE 3d 'tick the N longest options' solves {pct:.1f}% of "
                 f"multiple-response items (chance is 10%, max 25%)")

    # 3b — stub distractors. An option nobody would pick is padding, not a
    # distractor, and it silently turns a four-option question into a two-option one.
    def wrong_slots(r):
        if r["kind"] == "multi":
            return [i for i in range(MULTI_OPTS) if i not in r["answers"]]
        return [i for i in range(4) if i != r["answer"]]

    # Threshold calibrated against the exam guide's own sample items (section 8),
    # whose options run 27-86 characters with three of twelve under 45. A short
    # option is not automatically a stub: "Skip the analysis entirely." is 27
    # characters and a perfectly real position. What makes a stub is being too
    # short to state a position at all, which is nearer 25.
    stubs = sum(1 for r in rows for i in wrong_slots(r) if len(r["options"][i]) < 25)
    stub_pct = 100 * stubs / max(sum(len(wrong_slots(r)) for r in rows), 1)
    if stub_pct > 8:
        fail(f"GATE 3b {stub_pct:.1f}% of distractors are under 25 characters (max 8%) — stubs, not distractors")
    # Also recalibrated: the guide's third sample has a 3.19x spread, so a 2.5x
    # cap was stricter than the exam itself and was pushing options to be padded
    # to a uniform length, which is what made them read as statements rather than
    # as answers. Gate 3 above is the real protection — spread only matters if it
    # predicts the key, and gate 3 measures that directly.
    wide = sum(1 for r in rows
               if max(len(o) for o in r["options"]) > 3.5 * max(1, min(len(o) for o in r["options"])))
    alln = max(len(rows), 1)
    if 100 * wide / alln > 25:
        fail(f"GATE 3c {100*wide/alln:.1f}% of items have a >3.5x long/short option spread (max 25%)")

    # 4 — absolute-word tells
    tells = 0
    for r in single_rows:
        def loaded(text):
            return bool(ABSOLUTES.search(ABSOLUTE_EXEMPT.sub("", text)))
        if not loaded(r["correct"]) and all(loaded(r[k]) for k in ("d1", "d2", "d3")):
            tells += 1
    if 100 * tells / n > 10:
        fail(f"GATE 4 {100*tells/n:.1f}% of items put absolutes only in the distractors (max 10%)")

    # 5 — duplicate stems
    buckets = defaultdict(list)
    for r in rows:
        words = re.findall(r"[a-z]{4,}", r["stem"].lower())
        for key in sorted(set(words))[:6]:
            buckets[key].append(r)
    seen, dupes = set(), []
    for group in buckets.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                pair = tuple(sorted((a["source"], b["source"])))
                if pair in seen:
                    continue
                seen.add(pair)
                if SequenceMatcher(None, a["stem"], b["stem"]).ratio() > 0.85:
                    dupes.append(pair)
    if dupes:
        fail(f"GATE 5 {len(dupes)} near-duplicate stems, e.g. {dupes[:3]}")

    # 5b — duplicate correct answers inside a domain
    for d in DOMAINS:
        opts = Counter(r["raw"][0].lower() for r in rows if r["domain"] == d["id"])
        for text, c in opts.items():
            if c > 3:
                fail(f"GATE 5b {d['id']} reuses the same correct answer {c}x: '{text[:60]}'")

    # 6 — concept spread
    for d in DOMAINS:
        spread = Counter(r["concept"] for r in rows if r["domain"] == d["id"])
        for concept, count in spread.items():
            if count > CONCEPT_CAP:
                fail(f"GATE 6 {d['id']} concept '{concept}' has {count} items (max {CONCEPT_CAP})")

    # 7 — explanations must actually explain
    for r in rows:
        if len(r["why"].split()) < 10:
            fail(f"GATE 7 {r['source']} 'why' is too short to explain the answer")
        if len(r["traps"].split()) < 10:
            fail(f"GATE 7 {r['source']} 'traps' does not account for the distractors")

    # 8 — scenario framing. Medium-hard means applied judgement, not recall.
    for r in rows:
        if len(r["stem"].split()) < 12:
            fail(f"GATE 8 {r['source']} stem is only {len(r['stem'].split())} words — not a situation")
        if DEFINITIONAL.match(r["stem"]):
            fail(f"GATE 8 {r['source']} stem is a bare definition question")

    # 9 — tier mix. Commissioned as medium-hard: tier 2 is the floor, and the
    # bank must not drift into a wall of tier 4 either.
    tiers = Counter(r["tier"] for r in rows)
    if any(t < 2 or t > 4 for t in tiers):
        fail(f"GATE 9 tiers outside 2-4 present: {sorted(tiers)}")
    if 100 * tiers[2] / n > 30:
        fail(f"GATE 9 tier 2 is {100*tiers[2]/n:.1f}% of the bank (max 30%) — too easy for medium-hard")
    if 100 * tiers[4] / n > 35:
        fail(f"GATE 9 tier 4 is {100*tiers[4]/n:.1f}% of the bank (max 35%) — drifting past medium-hard")
    # The ladder has to actually exist: the exam rung dominates, both outer rungs
    # are genuinely present, and -- the part that matters for a candidate
    # drilling one domain -- every domain carries all three rungs, so a session
    # restricted to any single domain still ramps rather than sitting flat.
    if 100 * tiers[3] / n < 50:
        fail(f"GATE 9 tier 3 is only {100*tiers[3]/n:.1f}% of the bank (min 50%) — the exam rung must dominate")
    for t in (2, 4):
        if 100 * tiers[t] / n < 8:
            fail(f"GATE 9 tier {t} is only {100*tiers[t]/n:.1f}% of the bank (min 8%) — no usable difficulty ladder")
    for d in DOMAINS:
        per_tier = Counter(r["tier"] for r in rows if r["domain"] == d["id"])
        for t in (2, 3, 4):
            if per_tier[t] < 12:
                fail(f"GATE 9 {d['id']} has only {per_tier[t]} tier-{t} items (min 12) — ladder breaks in this domain")

    # 10 — multiple-response shape. The exam guide says each item states how many
    # responses to select, so "how many" has to be a real, answerable number: at
    # least two (or it is a single-answer item wearing a disguise) and at most
    # three of five (or the wrong answers become the easier thing to find).
    for r in multi_rows:
        if r["ncorrect"] not in (2, 3):
            fail(f"GATE 10 {r['source']} asks for {r['ncorrect']} correct of {MULTI_OPTS} (must be 2 or 3)")
        if len(set(o.lower() for o in r["options"])) != MULTI_OPTS:
            fail(f"GATE 10 {r['source']} has duplicate option text")
        if len(r["answers"]) != r["ncorrect"]:
            fail(f"GATE 10 {r['source']} placed {len(r['answers'])} answers, expected {r['ncorrect']}")

    # 11 — every item names an objective that exists in its own domain.
    obj_by_dom = {}
    if OBJECTIVES:
        for d, lst in OBJECTIVES["objectives"].items():
            obj_by_dom[d] = {o["id"] for o in lst}
        for r in rows:
            valid = obj_by_dom.get(r["domain"], set())
            if r["objective"] not in valid:
                fail(f"GATE 11 {r['source']} objective '{r['objective']}' is not one of {r['domain']}'s")

    # 12 — objective balance. The blueprint weights are per DOMAIN; the guide
    # writes items against the 30 objectives beneath them. A bank can sit exactly
    # on the domain weights and still leave an objective at zero, so each
    # objective has to hold a real share of its own domain.
    if OBJECTIVES:
        for d, lst in OBJECTIVES["objectives"].items():
            dom_rows = [r for r in rows if r["domain"] == d]
            if not dom_rows:
                continue
            per = Counter(r["objective"] for r in dom_rows)
            for o in lst:
                share = 100 * per[o["id"]] / len(dom_rows)
                if share < OBJ_MIN_SHARE:
                    fail_or_stage(f"GATE 12 objective {o['id']} holds {per[o['id']]} of {d}'s "
                         f"{len(dom_rows)} items ({share:.1f}%, min {OBJ_MIN_SHARE}%) — "
                         f"'{o['text'][:50]}'")

    # 13 — items must ask something. Every sample item in the exam guide ends in
    # an explicit question ("what is the most appropriate action?"). A scenario
    # with options attached is a prompt, not an exam item.
    flat = [r for r in rows if not INTERROGATIVE.search(r["stem"])]
    if flat:
        pct = 100 * len(flat) / max(len(rows), 1)
        fail_or_stage(f"GATE 13 {len(flat)} items ({pct:.1f}%) have no interrogative stem, "
             f"e.g. {flat[0]['source']} — an exam item asks a question")

    return fails, warns, {"ranks": dict(ranks), "tells": tells,
                          "counts": dict(singles), "multi": dict(multis), "tiers": dict(tiers)}


def main():
    loose = "--loose" in sys.argv
    report_only = "--report" in sys.argv

    rows, problems = parse()
    if problems:
        for p in problems[:20]:
            print("PARSE", p)
        if not loose:
            sys.exit(1)

    migrating = "--migrating" in sys.argv
    rows = place_answers(rows)
    fails, warns, stats = gates(rows, loose, migrating)

    print(f"parsed {len(rows)} questions across {len(set(r['domain'] for r in rows))} domains")
    print("  per domain:", {k: stats["counts"].get(k, 0) for k in COUNT})
    print("  multi-response:", stats.get("multi", {}), "total", sum(stats.get("multi", {}).values()))
    done = sum(1 for r in rows if INTERROGATIVE.search(r["stem"]))
    print(f"  exam-format rewrite: {done}/{len(rows)} items carry an interrogative stem "
          f"({100*done/max(len(rows),1):.1f}%)")
    print("  tiers:", dict(sorted(stats["tiers"].items())))
    n = max(len(rows), 1)
    print("  length-rank (1=longest):",
          {f"r{k+1}": f"{100*v/n:.1f}%" for k, v in sorted(stats["ranks"].items())})
    for w in warns[:40]:
        print("WARN ", w)
    if warns and len(warns) > 40:
        print(f"WARN  ... and {len(warns)-40} more")
    for f in fails[:40]:
        print("FAIL ", f)
    if fails:
        print(f"\n{len(fails)} gate failures — nothing written")
        sys.exit(1)

    print("all gates pass")
    if report_only:
        return

    concepts = defaultdict(lambda: defaultdict(int))
    for r in rows:
        concepts[r["domain"]][r["concept"]] += 1

    bank = {
        "meta": {
            "title": "Claude Certified Associate",
            "exam": "Claude Certified Associate – Foundations (CCAO-F)",
            "total": len(rows),
            "exam_questions": 60,
            "exam_minutes": 120,
            "pass_scaled": 720,
        },
        "domains": DOMAINS,
        "objectives": ({o["id"]: o["text"] for lst in OBJECTIVES["objectives"].values() for o in lst}
                       if OBJECTIVES else {}),
        "concepts": {d: dict(sorted(c.items())) for d, c in concepts.items()},
        "questions": [
            {
                "id": f"{r['domain']}-{i:04d}",
                "domain": r["domain"],
                "concept": r["concept"],
                "objective": r["objective"],
                "tier": r["tier"],
                "kind": r["kind"],
                "stem": r["stem"],
                "options": r["options"],
                # single-answer items carry `answer` (an index); multiple-response
                # items carry `answers` (a sorted list). The app branches on `kind`.
                **({"answers": r["answers"]} if r["kind"] == "multi" else {"answer": r["answer"]}),
                "why": r["why"],
                "traps": r["traps"],
            }
            for i, r in enumerate(rows)
        ],
    }
    out = SRC / "bank.json"
    out.write_text(json.dumps(bank, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
