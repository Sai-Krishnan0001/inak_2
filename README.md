# Claude Certified Associate — CCAO-F Practice Deck

**2,250 practice questions** for the **Claude Certified Associate – Foundations**
exam, built to Anthropic's own published exam guide.

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
| Exam code | CCAO-F |
| Questions | 60 |
| Item format | Multiple-choice **and multiple-response** — each item says how many to select |
| Time | 120 minutes |
| Pass mark | 720 on a 100–1,000 scale |
| Price | $99 USD |
| Delivery | Pearson VUE, online proctored or at a test centre |
| Validity | 12 months |
| Prerequisites | None |
| Retakes | 14 days, then 30, then 90; max four per rolling year |

Source: **Claude Certified Associate – Foundations Exam Guide, v1.0, July 2026**, linked from
the [Anthropic Partner Academy certifications page](https://anthropic-partners.skilljar.com/page/partner-certifications).
That guide is the authoritative document — read it before you book.

Two things worth checking before you book: the Associate credential **does not count
toward Claude Partner Network eligibility** (unlike the Developer and Architect exams),
and registration appears to require a partner-organisation email address.

## The seven domains

| Domain | Weight | Roughly, of the 60 |
|---|---|---|
| Output Evaluation and Validation | 21% | 13 |
| Workflow Integration and Solution Design | 16% | 10 |
| Governance, Risk, and Responsible Use | 15% | 9 |
| Prompting and Task Execution | 14% | 8 |
| Product and Model Selection | 12% | 7 |
| Configuration and Knowledge Management | 12% | 7 |
| Troubleshooting and Optimization | 10% | 6 |

Names and weights are reproduced from the exam guide's section 6. The guide also publishes
**30 second-level objectives** beneath these seven domains, and every question here is written
against one of them.

Output evaluation is the heaviest domain, and that is the shape of the job: the Associate's
core responsibility is deciding whether what came back is accurate, complete and fit to send.

## How to use it

**Two item formats, as the exam has.** Most questions are multiple-choice: four options, one
right. **146 are multiple-response**: five options, two or three right, and the question tells
you how many to pick. Those are marked all-or-nothing — half right is wrong — because that is
how the real exam scores them.

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

## Nothing is seen only once

Every question you answer is put on a review schedule. Get it right and it comes back
later — after a day, then three, then a week, then three weeks, then two months. **Get it
wrong and it drops to the front of the queue and returns in your very next session.**

Up to half of each session is drawn from whatever is due, so the questions you keep
missing keep finding you. The home screen shows how many are due, and a button runs a
session made only of those.

The deck also ramps. Each question is tagged core, exam or hard, and sessions weight
those by how you are doing in that domain: mostly core while you are below 60%, the exam
rung in the middle, and hard questions once you are past 80%. Your progress is stored in
your own browser and goes nowhere else.

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
- No near-duplicate questions, and no over-used topic within a domain. This one also
  took real work: a mid-build check found 400 near-duplicate pairs where a second set of
  questions had been produced by rewording the first. Those 545 questions were rewritten
  from scratch rather than shipped as padding.
- Every question is a scenario, never a bare definition.
- A genuine difficulty ladder in **every** domain — 293 core, 1,394 exam and 313 hard
  questions, with all three rungs present in each of the seven domains, so drilling a
  single domain still ramps.

## Where this comes from

Everything structural here — the seven domains and their weights, the 60/120/720 shape, the two
item formats, the $99 fee, the 12-month validity — is taken from **Anthropic's own CCAO-F exam
guide (v1.0, July 2026)**, not from third-party summaries. It is linked from the
[certifications page](https://anthropic-partners.skilljar.com/page/partner-certifications).

**Official preparation**, free and open without a partner login: the
[Claude Certified Associate – Foundations prep path](https://anthropic-partners.skilljar.com/path/claude-certified-associate-foundations)
— eight courses, about six and a half hours, one per domain. The exam guide itself also carries
three official sample questions with full rationale.

One thing to check early: while those courses are open, **registering for the exam requires a
partner email address on a recognised company domain.**

This deck is practice. The guide is the syllabus — read it.

## Coverage against the 30 objectives

The exam guide publishes 30 second-level objectives beneath the seven domains and says items
are written against them. **Every question here carries the objective it tests**, and
`reference/objectives.json` holds the mapping.

This matters because a bank can sit exactly on the domain weights and still never test an
objective. Before this pass, objective **3.4** (context limits and memory) had **zero**
questions across the whole bank; 2.5, 2.6, 1.4 and 5.2 were each under 2.5% of their domain.
The 110 questions added in this pass went entirely to those gaps.

**Work in progress:** the bank is being rewritten so every stem ends in an explicit question,
matching the format of the guide's own sample items. 150 of 2,250 are done. The build reports
the percentage on every run.
