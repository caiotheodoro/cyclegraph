"""Model runtimes. Deliberately outside `src/cyclegraph/`.

`docs/DECISIONS.md` D022: 100DOH needs torch and the `signal` extra declares none, so the
runtimes live here and `src/cyclegraph/signal/` consumes the files they write. The payoff is
that every estimator in this repository is testable with no model installed at all.

Nothing here is unit-tested, because it cannot be without the weights and a GPU. What IS
tested is everything around it -- `tests/test_run_detector.py` drives the orchestration with a
fake detector -- so a failure here is a failure to load a model, not a silent wrong answer.
"""
