# ccao-deck

A **2,250-question practice deck** for the **Claude Certified Associate – Foundations
(CCAO-F)** exam — seven blueprint domains, medium-hard, discrete items in both of the
exam's two formats — plus a
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
| d1 | Prompting and Task Execution | 14% | 280 + 20 |
| d2 | Output Evaluation and Validation | 21% | 416 + 29 |
| d3 | Product and Model Selection | 12% | 240 + 17 |
| d4 | Workflow Integration and Solution Design | 16% | 320 + 22 |
| d5 | Configuration and Knowledge Management | 12% | 240 + 17 |
| d6 | Governance, Risk, and Responsible Use | 15% | 304 + 21 |
| d7 | Troubleshooting and Optimization | 10% | 200 + 14 |

Counts are `single-answer + multiple-response`. Domain **names are the exam guide's**, because
they are what appears on a candidate's score report.

Domain weights come from the published exam guide (cross-checked across two independent
sources); the counts differ slightly from the weights because **every domain count must
divide by 4** for the answer-key balance gate — 21% would be 420, which does not, so d2
holds 416. Session weighting uses the true blueprint percentages, not the bank counts.

## Stack

Plain HTML/CSS/JS, no framework, no runtime dependencies. Python 3 at build time only.
Styling is the `interface` skill's Aurora Nocturne, inlined at build. **No mascot** —
the user chose none for this build, as they did for `ccaf-plain`.

## Layout

| Path | Purpose |
|---|---|
| `index.html` | **The deliverable.** Self-contained, ~1.8 MB, opens anywhere |
| `src/authored/dN-XX.psv` | Single-answer questions. 51 files, 9 fields, pipe-separated |
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

1. **Domain counts** — exact per-domain counts per item shape, 2,140 total.
2. **Answer-position balance** — exactly count/4 per letter per domain, no run of three.
3. **Length must not predict the answer** — "always pick the *n*th-longest option" must
   score under 34% for every *n* (chance is 25%).
4. **3b/3c — stub distractors and spread.** Under 8% of distractors below 35 characters,
   and under 25% of items with a >2.5x long/short spread.
5. **Absolute-word tells** — items where only distractors carry "always/never/only" stay under 10%.
6. **Duplicate stems** — zero pairs above 85% similarity; no correct answer reused >3x in a domain.
7. **Explanations** — `why` and `traps` both substantive.
8. **Scenario framing** — no stem under 12 words, none phrased as a bare definition.
9. **Tier mix and ladder** — tier 2 under 30% and tier 4 under 35% so the bank stays
   medium-hard, tier 3 at least 50%, both outer rungs at least 8%, and **at least 12 items
   per tier in every domain** so a single-domain session still ramps.

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

- **Reworded questions are not new questions.** A second thousand authored for d3, d4 and
  d5 turned out to be the first thousand restated — gate 5 found 400 near-duplicate pairs.
  d2-06..08, d3-04..06, d4-05..08 and d5-04/05 were rewritten from scratch (545 questions
  in total). When extending the bank, run gate 5 *before* trusting a batch.
- **Do not relax a gate to fit the data.** d2-d4 originally had almost no tier-2 or tier-4
  items, and GATE 9's ladder check was briefly loosened to accommodate that. The honest fix
  was to author the missing rungs during the rewrite; the strict thresholds are back.
- **The review schedule is in `app.js`, not the bank.** Leitner boxes at 0/1/3/7/21/60 days,
  keyed by question id in `localStorage` under `ccao.deck.v2` (v1 state migrates in). A
  wrong answer resets to box 0, which makes it due immediately. `draw()` fills up to half a
  session from what is due, then unseen, then weak topics; `tierWeights()` shifts the
  core/exam/hard mix by the learner's accuracy in that domain.

## The two item shapes

The exam guide (section 5) specifies "Multiple-choice and multiple-response items; each item
states how many responses to select". The deck carries both.

- **`src/authored/dN-XX.psv`** — 9 fields, 4 options, exactly one correct, written first.
  Gate 2 gives these an exactly balanced answer key.
- **`src/authored/dN-mX.psv`** — 11 fields: `concept|tier|ncorrect|stem|o1..o5|why|traps`.
  Five options; the first `ncorrect` (2 or 3) are the correct ones. There is no clean
  per-letter quota available here, so **gate 2b** checks the weaker property instead: no slot
  is correct disproportionately often. **Gate 3d** is the length leak for this shape — "tick
  the N longest options" must not beat 25%.

The app scores multiple-response **all-or-nothing** (partial selections are wrong, as on the
real exam) and renders the "Select two responses." line from `ncorrect` rather than trusting
each stem to carry it.

## Content validity, not just statistical hygiene

The gates measure whether the bank is internally fair. None of them measures whether it is
about the right things. The exam guide's **30 second-level objectives** are the content
standard; `shared/ccao/SYLLABUS.md` lists them in full.

The 140 multiple-response items were written to close measured gaps against those objectives.
Before this pass, **connectors (Google Drive, Gmail) had zero coverage** across 2,000 questions
despite being objective 5.2; research mode, brainstorming, the model family names and audience
adaptation were all similarly thin.

**Before adding questions, check coverage against the 30 objectives — not just the seven
domain headings.** A bank can sit perfectly on the domain weights and still miss an objective
entirely, which is exactly what happened here.

## The objective field, and gates 11-13

Every question carries `objective` — one of the 30 second-level objectives published in the
exam guide's section 6, listed in `shared/ccao/objectives.json` (copied to `reference/`).

- **Gate 11** — the objective must be one of that domain's.
- **Gate 12** — each objective must hold at least 12% of its own domain. This is the content
  gate the CCA-F projects never had: domain weights alone do not make a bank valid.
- **Gate 13** — every stem must end in an interrogative. All three sample items in the guide
  do; a scenario with options attached is a prompt, not an exam item.

Gates 12 and 13 are **hard gates** that the bank does not yet meet. `--migrating` stages them
as warnings so partial progress can ship, and the build prints how far the rewrite has got.
**Remove the flag once the rewrite is complete** — it exists to keep the shortfall visible,
not to lower the bar.

## Two calibrations taken from the guide's sample items

The guide's three samples (section 8) have options running **27-86 characters** with spreads up
to **3.19x**. The deck's own gates were stricter than the real exam: a 45-character floor and a
2.5x spread cap. That floor was forcing options to be padded to a uniform length, which is part
of why they read as statements rather than as answers. Gate 3b now uses 25 characters and gate
3c allows 3.5x. **Gate 3 — length must not predict the key — is the real protection and is
unchanged.**
