# Methodology

The shared thesis behind `assay`, `reconforge`, `lossbench`, `vernier` and `titer` — and
where cyclegraph departs from it.

## The shared part

> A finding is not a result until you know what it is worth, and a measurement is not a
> result until you know its uncertainty.

In practice that has meant: freeze the protocol before the data; publish the interval, not
the point; cluster over the unit that actually repeats; write the coverage gaps in someone
else's vocabulary; open the red team before there are results to defend; generate the card
rather than transcribe it; and keep the unflattering number in the README.

The family's strongest form of that bet is **find a task where the ground truth is a
program, not an opinion** — the forge line's whole design, where a deterministic oracle
recomputes violations from a rendered artifact and no model is ever asked for a verdict.

## Where cyclegraph departs, and it is a real departure

**There is no oracle here.** Not a program, not a panel, not a person.

Hand Activity Level is a construct from occupational health, and the only ground truth for
it is a certified ergonomist's judgement. cyclegraph has none — `docs/DECISIONS.md` D009 —
so it cannot do what the forge line does and cannot do what `vernier` does either, since
`vernier` at least collected human labels against a written rubric.

What is left is weaker and the project says so rather than dressing it up:

1. **Internal consistency in place of accuracy.** H1, H2 and H5 test whether the instrument
   agrees with itself across label sources, sampling rates, estimation methods and
   clustering assumptions. Consistency is necessary and nowhere near sufficient.
2. **A negative control in place of a positive one.** The pipeline must separate factory
   work from non-repetitive work. That bounds what it *cannot* be measuring without
   establishing what it is.
3. **Literature plausibility in place of agreement.** H3 compares a distribution against
   published values. It is directional and labelled as such everywhere it appears.
4. **The argument carries more weight than usual.** The claim that a quality metric is
   dimensionally an exposure primitive is checkable by inspection rather than by experiment.
   If the argument is wrong — `docs/RED-TEAM.md` A3 — no amount of internal consistency
   saves it.

The honest summary: this project is further from a program-as-oracle than any of its
siblings, and its published verdict is `NOT_VERIFIED` by construction rather than by
accident.

## The rule that does not relax

Nothing is reported at a unit any person or site could be identified by. That constraint
comes from `docs/ETHICS.md` rather than from the methodology, and unlike everything above it
is not a trade-off to be optimised.
