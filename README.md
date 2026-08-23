# Claude Certified Associate — CCAO-F Practice Deck

A thousand practice questions for the **Claude Certified Associate – Foundations**
exam, weighted to the published blueprint.

**Open `index.html` in any browser.** That is the whole thing — one self-contained
file, no install, no internet needed, works offline.

---

## What the exam is

CCAO-F is Anthropic's non-developer credential. It tests whether you can put Claude to
work on real business tasks: prompting well, judging whether output is good enough to
send, picking the right model and product surface, setting up Projects, and using AI
responsibly. No API, no code, no software background required.

|  |  |
|---|---|
| Questions | 60 |
| Time | 120 minutes |
| Pass mark | 720 on a 100–1000 scale |
| Price | $99 |
| Delivery | Pearson VUE, online or at a test centre |

Two things worth checking before you book: the Associate credential **does not count
toward Claude Partner Network eligibility** (unlike the Developer and Architect exams),
and registration appears to require a partner-organisation email address.

## The seven domains

| Domain | Weight | Roughly, of the 60 |
|---|---|---|
| Output Evaluation & Validation | 21% | 13 |
| Workflow Integration & Design | 16% | 10 |
| Governance, Risk & Responsible Use | 15% | 9 |
| Prompting & Task Execution | 14% | 8 |
| Product & Model Selection | 12% | 7 |
| Configuration & Knowledge Management | 12% | 7 |
| Troubleshooting & Optimisation | 10% | 6 |

Output evaluation is the heaviest domain, and that is the shape of the job: the Associate's
core responsibility is deciding whether what came back is accurate, complete and fit to send.

## How to use it

**Practice mode** marks each answer the moment you commit to it, then shows why the right
answer wins and what made each wrong one tempting. This is the mode for learning.

**Exam simulation** holds everything back until you submit, gives you a two-minute-per-question
clock, lets you move back and change answers, and scores you on the 100–1000 scale against the
720 pass mark. This is the mode for finding out where you stand.

Pick your mode, how many questions, and which domains, on the home screen. Whatever you
pick is drawn to the real blueprint weights, so even a short run has the shape of the exam.

**The Bank** is every question open-book, searchable, with the answers and explanations
showing. Use it to settle a doubt rather than to be tested. Anything you flag during a
session waits for you there.

## A note on the score

A 10 or 20-question run is a drill, not a verdict — the margin of error on a sample that
small is wide, and the app will say so. Sit a full 60-question exam simulation before
reading anything into the number. A domain with fewer than three questions drawn is
labelled *Thin* rather than Strong or Weak, for the same reason.

## How the questions were built

Every question is a workplace situation with four plausible answers. The quality gates
that had to pass before the deck would build:

- The correct answer sits in each of the four positions an equal number of times within
  every domain, with no run of three the same.
- **Length carries no signal.** "Always pick the longest option" and every other
  length-based strategy scores under 34% against a 25% chance baseline. This one took real
  work — the first full build had the correct answer as the longest option 87.6% of the
  time, which would have let anyone beat the deck without reading it.
- No stub answers. Every distractor is a position someone could actually hold, so a
  four-option question is never quietly a two-option one.
- No near-duplicate questions, and no over-used topic within a domain.
- Every question is a scenario, never a bare definition.

Domain weights were taken from the published exam guide and cross-checked across two
independent sources. Anthropic's own exam guide is the authoritative scope document — check
it before you study to these weights.
