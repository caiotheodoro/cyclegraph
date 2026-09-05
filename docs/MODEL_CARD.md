# Model card

**cyclegraph releases no model, and v1 will not.**

This file exists to say that plainly rather than to leave a reader wondering whether one is
coming.

## Why there is no model

The pipeline needs a per-frame manipulation label at a cost that scales to tens of millions
of frames. It does not need a *new* model to produce one. `docs/METHOD.md` E3 uses a frozen
backbone plus a linear head — the shape `../vernier` already built, published, and reported
as a negative result at 0.693 fidelity against a 0.8 target.

Reusing a published negative result as a component is deliberate. Its failure is documented,
so its contribution to error is bounded by something a reader can go and check, and H1 is
the test that decides whether that bound is good enough to scale.

## If that changes

A trained model would need its own card with, at minimum: the training data and its
provenance under `docs/ETHICS.md`'s basis, per-class performance, the population it was
fitted on, and the population it would fail on. Training on this corpus would raise a
consent question that `docs/ETHICS.md` does not currently answer — the document permits
*measurement* of the recordings, and says nothing about fitting parameters to them.

**Resolving trigger:** any decision to train on this corpus goes through a
`docs/DECISIONS.md` entry and an amendment to `docs/ETHICS.md`, in that order, before a
single gradient step.
