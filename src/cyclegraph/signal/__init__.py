"""Per-frame manipulation, hand boxes, flow samples, and residual hand speed.

Deliberately empty of re-exports, for the reason `cyclegraph.corpus` gives.

`docs/ARCHITECTURE.md`: `label_source` is carried, never defaulted; a missing hand or a
failed flow is `null` with a reason, never zero. No model runtime lives in this package --
100DOH needs torch and a judge needs an HTTP client, neither of which the `signal` extra
declares, so both are satisfied here by file-backed stores and run from `scripts/`.
"""
