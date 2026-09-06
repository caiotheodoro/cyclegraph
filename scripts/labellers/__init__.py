"""Label sources. Outside `src/cyclegraph/` for the reason `scripts/detectors/` is
(`docs/DECISIONS.md` D022): a backbone needs torch, the `signal` extra declares none, and
keeping runtimes here is what lets every estimator be tested with no model installed.
"""
