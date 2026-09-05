# Reproduction

How a third party re-runs this end to end. The standard cyclegraph applies to a vendor's
measurement applies here first: if this document does not let a stranger obtain commensurable
numbers, the project has failed on its own terms.

**Current state: there is nothing to reproduce.** W0 is documentation only. What follows is
the path as it is being built, and the free portion of it is already real.

## Prerequisites

- Python 3.11 or later.
- `ffmpeg` on `PATH`, built with `https` and `tls` protocol support. Check with
  `ffmpeg -protocols | grep -E 'https|subfile'`; the corpus path needs both.
- For anything touching the corpus: a Hugging Face token with `builddotai/Egocentric-10K`'s
  terms accepted. The dataset is gated. Put it in `.env`; see `.env.example`.
- For E6 onward: the ACGIH TLV documentation for Hand Activity Level. It is a purchase and
  there is no free substitute. `docs/RUBRIC.md` records why an approximation is refused.

## The free path — $0, no token, no network

Everything that verifies the repository's internal consistency runs offline.

```
git clone <this repo> && cd cyclegraph
pip install -e ".[dev]"
make validate
```

That runs the privacy gate, the placeholder gate, the cited-path gate, the test suite and
`mypy --strict`. It is the whole of W0's deliverable and it passes with `src/` empty — which
is the point: the gates work on documentation alone, so the ordering claim is checkable
before any code exists.

## The paid path

Costs are estimates under stated assumptions until each stage runs; `docs/METHOD.md` carries
the assumption beside each figure and replaces it with a measured value as it lands.

```
make manifest FACTORY=factory_001    # E1. Negligible: shard index reads only.
make signal                          # E2+E3. ~1.7M frames for the pilot factory.
make cycles                          # E5. Negligible.
make hal                             # E6. BLOCKED until docs/SURVEY.md S3 resolves.
make estimate                        # E8. Minutes.
make card                            # E9. Exits nonzero while the verdict is NOT_VERIFIED.
```

Every stage that is not written yet fails loudly with a pointer to the wave that lands it.
That is deliberate — a stage that silently no-ops is how a pipeline comes to look finished
before it is.

## Known footguns

- **`make hal` is meant to fail** right now. It is blocked on the scale mapping, not broken.
- **The evaluation release will not work.** Its `frame_id` carries no clip linkage, so no
  duty cycle can be computed from it. Use the raw release. `docs/DECISIONS.md` D011.
- **A shallow clone breaks the ordering check.** `git log --diff-filter=A` needs full
  history to show that every document predates the first `src/` file.
- **Re-pinning the corpus revision invalidates every stored record.** `corpus_rev` is on the
  record for exactly this reason; records from two revisions are never pooled, and the
  pipeline will refuse rather than mix them.
- **Reproducing the numbers does not reproduce the validation.** There is none. No
  ergonomist scored this corpus, and running these commands successfully does not change
  that. `docs/COVERAGE.md`.
