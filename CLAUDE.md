# ccao-deck

A **1,000-question practice deck** for the **Claude Certified Associate – Foundations
(CCAO-F)** exam — seven blueprint domains, medium-hard, all case-scenario — plus a
self-contained drill app with a practice mode and an exam simulation.

Built to be handed to someone else who is sitting the exam. It assumes no coding
background: CCAO-F is the programme's non-developer credential.

## The exam this targets

CCAO-F is **not** the exam `active/ccaf-*` targets. Those are all Claude Certified
**Architect** – Foundations (CCAR-F, five domains, 27/18/20/20/15). CCAO-F is the
**Associate** credential: seven domains, non-technical, $99, 60 questions, 120 minutes,
720/1000 to pass, delivered by Pearson VUE.

| # | Domain | Weight | Held here |
|---|---|---|---|
| d1 | Prompting & Task Execution | 14% | 140 |
| d2 | Output Evaluation & Validation | 21% | 208 |
| d3 | Product & Model Selection | 12% | 120 |
| d4 | Workflow Integration & Design | 16% | 160 |
| d5 | Configuration & Knowledge | 12% | 120 |
| d6 | Governance, Risk & Responsible Use | 15% | 152 |
| d7 | Troubleshooting & Optimisation | 10% | 100 |

Domain weights come from the published exam guide (cross-checked across two independent
sources); the counts differ slightly from the weights because **every domain count must
divide by 4** for the answer-key balance gate — 21% would be 210, which does not, so d2
holds 208. Session weighting uses the true blueprint percentages, not the bank counts.

## Stack

Plain HTML/CSS/JS, no framework, no runtime dependencies. Python 3 at build time only.
Styling is the `interface` skill's Aurora Nocturne, inlined at build. **No mascot** —
the user chose none for this build, as they did for `ccaf-plain`.

## Layout

| Path | Purpose |
|---|---|
| `index.html` | **The deliverable.** Self-contained, ~912 KB, opens anywhere |
| `src/authored/dN-XX.psv` | The questions. Source of truth, 26 files, pipe-separated |
| `src/build_bank.py` | Parses, places the answer key, runs the gates, emits `bank.json` |
| `src/bank.json` | Built bank. Generated — never edit |
| `src/parity.py` | Length-parity worklist + a TSV applier for option rewrites |
| `src/trim_options.py` | Deletes justifying tails from over-long distractors |
| `src/analyse_leaks.py` | Per-file report on the correct-answer length rank |
| `src/app.css`, `src/app.js` | Project styles and the drill engine |
| `src/index.template.html` | Shell with `/*__TOKEN__*/` placeholders for inlining |

## Build

```bash
python3 src/build_bank.py && python3 src/build_html.py
```

`build_bank.py` places the answer key **then** runs the gates and refuses to emit if any
fail. `--report` gates without emitting; `--loose` warns instead of failing (authoring only).

Preview with the `ccao-deck` entry in the workspace `.claude/launch.json` (serves on 8477).

## Authoring format

One question per line, nine pipe-separated fields:

```
concept|tier|stem|CORRECT|distractor|distractor|distractor|why|traps
```

Domain comes from the filename (`d3-02.psv` → d3). Tier is 2 (core), 3 (exam) or 4 (hard).
**Write the correct answer first every time** — `build_bank.py` places it.
`why` explains why the right answer wins; `traps` accounts for what made each wrong one
tempting. Both are shown in practice mode and in the Bank.

## The gates

1. **Domain counts** — exact per-domain counts, 1,000 total.
2. **Answer-position balance** — exactly count/4 per letter per domain, no run of three.
3. **Length must not predict the answer** — "always pick the *n*th-longest option" must
   score under 34% for every *n* (chance is 25%).
4. **3b/3c — stub distractors and spread.** Under 8% of distractors below 35 characters,
   and under 25% of items with a >2.5x long/short spread.
5. **Absolute-word tells** — items where only distractors carry "always/never/only" stay under 10%.
6. **Duplicate stems** — zero pairs above 85% similarity; no correct answer reused >3x in a domain.
7. **Explanations** — `why` and `traps` both substantive.
8. **Scenario framing** — no stem under 12 words, none phrased as a bare definition.
9. **Tier mix** — tier 2 under 30%, tier 4 under 35%, so the bank stays medium-hard.

## Gotchas

- **Never edit `src/bank.json`.** Edit the `.psv` files and rebuild.
- **The correct answer goes first in the source.** Hand-placing it defeats gate 2.
- **`|` is the delimiter** — it cannot appear in any field.
- **The length leak is the failure mode to watch.** First full build measured *87.6%* of
  correct answers as the longest option — a test-taker who read nothing and picked the
  longest would have scored 87.6%. The cause is an authoring habit: correct answers get
  written fuller than distractors, because the justification gets appended to them.
  It was closed to 29/26/25/21 by (a) retargeting correct answers across each item's own
  distractor spread via `parity.py`, (b) `trim_options.py` deleting justifying tails from
  140–160 character distractors, and (c) expanding genuinely thin distractors.
  **Re-run `analyse_leaks.py` after any authoring session.**
- **Mechanical trimming alone does not work** — it just moves the bulge. Measured: trimming
  every justification tail took "longest" from 87.6% to 46.8%, with "shortest" rising to
  44.0%. Four options of genuinely similar length is the only thing that holds.
- **`parity.py apply` takes `source<TAB>field<TAB>text`** where field is 3 (correct) or
  4/5/6 (distractors). Multiple edits to the same line are supported.
- **`trim_options.py` is a pure deletion** and never invents text, but re-read what it
  changed before trusting it — its `TARGET` has been walked down to 78 and the clean cuts
  are exhausted.
- **Answer positions are a property of the built bank.** The engine deliberately does *not*
  reshuffle options at runtime, which would destroy the balance.
- **Session length, mode and domain scope are chosen in the app**, never asked in chat.
- **Both feedback modes exist because the user asked for both** — practice marks on commit,
  exam holds until submit. Do not collapse them.

## Engine notes

- `localStorage` key `ccao.deck.v1` holds `seen` (no-repeat), `topics` (per-concept accuracy,
  drives adaptation), `doubts` (flags) and `history`.
- Up to 40% of each domain's slots go to concepts previously answered below 70%.
- Domain chips filter the draw; blueprint weights are re-normalised across whichever
  domains are live, by largest remainder.
- The scaled score only counts domains actually drawn, re-normalised to their weights.
- Exam mode allows a 2-minute-per-question clock and free navigation; practice mode locks
  a question once checked.
- A domain with fewer than 3 questions drawn is labelled **Thin**, never Strong/Weak.
- `[hidden]{display:none !important}` is load-bearing — `.pill` sets `display`, which
  otherwise beats the `hidden` attribute and leaves an empty timer pill visible.
