# Retractions

Empty by design, committed at W0, before there was anything to retract.

The file exists first so that retracting costs nothing structural later. A project that adds
a retractions document only once it needs one has already made the decision harder than it
should be.

## What goes here

Any published claim of this project's that is later found wrong, with: the claim as
published, what was actually true, how it was found, and what changed so it would be caught
earlier next time. Entries are appended and never edited.

The sibling precedent is `reconforge`, whose README still leads with its headline and
retracts it in a box directly underneath — a pre-registered across-seed test fired, and the
spread was 2.86× the claimed margin. That is the standard: the retraction sits with the
claim, not in a footnote.

## Entries

Three entries, all dated 2026-11-23, all the same defect: a claim read off one texture seed.
`scripts/measure_flow_gain_seeds.py` repeated the sweep over 20 seeds (11 for RAFT-small) and
`results/flow_gain_seeds.json` holds the result. Seed 11 reproduces the published curves exactly
at all four decode widths (`tests/test_paper.py`), so none of the earlier numbers is wrong as a
record of that seed. What was wrong is what each was taken to show. The essay
`writing/flow-is-not-hand-speed.md`, the Hugging Face dataset card and the Space were published
before this and carry the single-seed reading; the essay now opens with a correction, and the
paper (`paper/cyclegraph.tex`) carries the seed spread.

### R1. "Gain falls off a cliff between 22.8 and 34.2 px"

**As published** (essay, benchmark card, dataset card): gain holds near one, falls off a cliff
between two grid points and lands on a shelf. **What is true:** the shelf is real and survives
the seeds. The cliff is a transition whose location depends on the texture. On a fine grid across
it the half-way crossing varies by several pixels between seeds, and 7 of 20 seeds are
already below 0.9 at 22.8 px, where the published seed reads 0.99. **How found:** the seed sweep,
run to give every number a spread. **What changed:** a seed arm, a gate tying it to the published
file, and a paper that quotes the spread.

### R2. "960x540 is a measured optimum; 1920x1080 does worse than 480x270"

**As published:** the decode-resolution table, one seed, read as an optimum. **What is true:** at
the same physical motion the seed ranges of 480x270 and 960x540 overlap almost entirely, so no
optimum is shown. 1920x1080 does fall at a lower physical speed than 480x270, as claimed, but so
does 1440x810, and the grid is too coarse above 480 to say how the crossing scales with the hand
box. The decode choice in D050 was made on this table. **What changed:** D050's reasoning is
unchanged where it rests on the physical speed at which the larger decodes collapse, and does not
stand where it rests on 960x540 beating 480x270.

### R3. "RAFT-small holds full gain at 34.2 px where Farneback has collapsed"

**As published:** RAFT-small 0.9738 against Farneback 0.2024 at 34.181 px. **What is true:** over
the seeds RAFT-small's mean gain there is 0.80, with a range of 0.58 to 0.97. RAFT-small does cross
one half later than Farneback, with non-overlapping ranges on the same grid, and lands on the same
shelf. "Holds full gain" was a seed 11 statement.
